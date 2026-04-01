# codegen.py — Gerador de Código para a EWVM (European Web Virtual Machine)

# Duas passagens:
#   1. scan_memory — percorre a AST e aloca endereços de memória para todas as variáveis
#   2. generate    — percorre a AST e emite instruções EWVM

# Padrão WHILE: deteção de  N IF(cond) THEN ... GOTO N ENDIF
# e geração de ciclo estruturado em vez de labels/jumps avulsos.


class CodeGenerator:

    def __init__(self):
        self.code:          list  = []
        self.var_addresses: dict  = {}   # "scope_varname" - endereço global
        self.var_count:     int   = 0
        self.functions:     dict  = {}   # nome → lista de parâmetros
        self.label_counter: int   = 0
        self.do_contexts:   dict  = {}   # label_fortran - contexto do DO
        self.arrays:        dict  = {}   # "scope_varname" - tamanho
        self._while_done:   set   = set()  # labels já emitidos como while

    # Utilitários

    def _new_label(self) -> str:
        self.label_counter += 1
        return f"L{self.label_counter}"

    def _addr(self, scope: str, var: str) -> int:
        return self.var_addresses[f"{scope}_{var}"]

    def _emit(self, *instructions: str):
        self.code.extend(instructions)

    # PASSAGEM 1 — ALOCAÇÃO DE MEMÓRIA

    def scan_memory(self, node, scope: str = ''):
        if node is None: return
        if isinstance(node, list):
            for n in node: self.scan_memory(n, scope)
            return
        if not isinstance(node, tuple): return

        kind = node[0]
        scanner = getattr(self, f'_scan_{kind}', self._scan_recurse)
        scanner(node, scope)

    def _scan_recurse(self, node, scope):
        for child in node[1:]:
            self.scan_memory(child, scope)

    def _scan_compilation_unit(self, node, _scope):
        for unit in node[1]: self.scan_memory(unit)

    def _scan_program(self, node, _scope):
        self.scan_memory(node[2], node[1])

    def _scan_function(self, node, _scope):
        _, _type, name, params, body = node
        self.functions[name] = params
        # A variável de retorno tem o mesmo nome da função
        self.var_addresses[f"{name}_{name}"] = self.var_count
        self.var_count += 1
        for p in params:
            self.var_addresses[f"{name}_{p}"] = self.var_count
            self.var_count += 1
        self.scan_memory(body, name)

    def _scan_subroutine(self, node, _scope):
        _, name, params, body = node
        self.functions[name] = params
        for p in params:
            self.var_addresses[f"{name}_{p}"] = self.var_count
            self.var_count += 1
        self.scan_memory(body, name)

    def _scan_declare(self, node, scope):
        for item in node[2]:
            if item[0] == 'id':
                key = f"{scope}_{item[1]}"
                if key not in self.var_addresses:
                    self.var_addresses[key] = self.var_count
                    self.var_count += 1
            elif item[0] == 'array':
                key = f"{scope}_{item[1]}"
                if key not in self.var_addresses:
                    self.var_addresses[key] = self.var_count
                    self.var_count += item[2]
                    self.arrays[key] = item[2]

    def _scan_if(self, node, scope):
        self.scan_memory(node[1], scope)
        self.scan_memory(node[2], scope)

    def _scan_if_else(self, node, scope):
        self.scan_memory(node[1], scope)
        self.scan_memory(node[2], scope)
        self.scan_memory(node[3], scope)

    def _scan_do(self, node, scope):
        self.scan_memory(node[3], scope)
        self.scan_memory(node[4], scope)

    def _scan_do_step(self, node, scope):
        self.scan_memory(node[3], scope)
        self.scan_memory(node[4], scope)
        self.scan_memory(node[5], scope)

    def _scan_label(self, node, scope):
        self.scan_memory(node[2], scope)

    # PASSAGEM 2 — GERAÇÃO DE CÓDIGO
    def generate(self, node, scope: str = ''):
        if node is None: return
        if isinstance(node, list):
            for n in node: self.generate(n, scope)
            return
        if not isinstance(node, tuple): return

        kind = node[0]
        generator = getattr(self, f'_codgen_{kind}', None)
        if generator:
            generator(node, scope)

    # Estrutura do programa

    def _codgen_compilation_unit(self, node, _scope):
        # Reserva memória global para todas as variáveis
        for _ in range(self.var_count):
            self._emit("pushi 0")

        program = next((u for u in node[1] if u[0] == 'program'), None)
        funcs   = [u for u in node[1] if u[0] in ('function', 'subroutine')]

        self._emit("start")
        # Inicializa arrays (alloc + storeg)
        for arr_key, size in self.arrays.items():
            addr = self.var_addresses[arr_key]
            self._emit(f"alloc {size}", f"storeg {addr}")

        self.generate(program)
        self._emit("stop")
        for f in funcs:
            self.generate(f)

    def _codgen_program(self, node, _scope):
        self.generate(node[2], node[1])

    def _codgen_function(self, node, _scope):
        name = node[2]
        self._emit(f"{name}:")
        self.generate(node[4], name)
        #if not self._last_stmt_is_return(node[3]):
            #self._emit("return")

    def _codgen_subroutine(self, node, _scope):
        name = node[1]
        self._emit(f"{name}:")
        self.generate(node[3], name)
       #if not self._last_stmt_is_return(node[3]):
            #self._emit("return")

    def _last_stmt_is_return(self, stmts) -> bool:
        """Verifica se o último statement de um bloco é um RETURN."""
        if not isinstance(stmts, list) or not stmts:
            return False
        last = stmts[-1]
        print(f"DEBUG: Último statement: {last}")
        if isinstance(last, tuple):
            return last[0] == 'return'
        return False

    # Declarações (apenas registadas no scan, não geram código)

    def _codgen_declare(self, node, scope): pass
    def _codgen_continue(self, node, scope): pass
    def _codgen_return(self, node, scope): self._emit("return")

    # Atribuições

    def _codgen_assign(self, node, scope):
        _, var, expr = node
        self.generate(expr, scope)
        self._emit(f"storeg {self._addr(scope, var)}")

    def _codgen_assign_array(self, node, scope):
        _, var, idx, val = node
        self._emit(f"pushg {self._addr(scope, var)}")
        self.generate(idx, scope)
        self._emit("pushi 1", "sub")
        self.generate(val, scope)
        self._emit("storen")

    # I/O - Prints e Reads

    def _codgen_print(self, node, scope):
        for item in node[1]:
            if isinstance(item, tuple) and item[0] == 'string':
                txt = item[1].replace('"', '\\"')
                self._emit(f'pushs "{txt}"', "writes")
            elif isinstance(item, tuple) and item[0] == 'real':
                self.generate(item, scope)
                self._emit("writef")
            else:
                self.generate(item, scope)
                self._emit("writei")
        self._emit("writeln")

    def _codgen_read(self, node, scope):
        self._emit("read", "atoi", f"storeg {self._addr(scope, node[1])}")

    def _codgen_read_array(self, node, scope):
        _, var, idx = node
        self._emit(f"pushg {self._addr(scope, var)}")
        self.generate(idx, scope)
        self._emit("pushi 1", "sub", "read", "atoi", "storen")

    # Expressões

    def _codgen_number(self, node, _scope):
        self._emit(f"pushi {node[1]}")

    def _codgen_real(self, node, _scope):
        self._emit(f"pushf {node[1]}")

    def _codgen_bool(self, node, _scope):
        self._emit("pushi 1" if node[1] == '.TRUE.' else "pushi 0")

    def _codgen_string(self, node, _scope):
        txt = node[1].replace('"', '\\"')
        self._emit(f'pushs "{txt}"')

    def _codgen_id(self, node, scope):
        self._emit(f"pushg {self._addr(scope, node[1])}")

    def _codgen_uminus(self, node, scope):
        inner = node[1]
        if inner[0] == 'number':
            self._emit(f"pushi {-inner[1]}")
        elif inner[0] == 'real':
            self._emit(f"pushf {-inner[1]}")
        else:
            self.generate(inner, scope)
            self._emit("pushi -1", "mul")

    def _codgen_binop(self, node, scope):
        _, op, left, right = node
        self.generate(left, scope)
        self.generate(right, scope)
        ops = {
            '+': 'add',    '-': 'sub',    '*': 'mul',    '/': 'div',
            '.EQ.': 'equal', '.GT.': 'sup', '.GE.': 'supeq',
            '.LT.': 'inf',   '.LE.': 'infeq',
        }
        if op in ops:
            self._emit(ops[op])
        elif op == '.NE.':
            self._emit("equal", "pushi 0", "equal")
        elif op == '.AND.':
            self._emit("mul")
        elif op == '.OR.':
            self._emit("add", "pushi 0", "sup")

    def _codgen_not(self, node, scope):
        self.generate(node[1], scope)
        self._emit("pushi 0", "equal")

    def _codgen_mod_call(self, node, scope):
        self.generate(node[1], scope)
        self.generate(node[2], scope)
        self._emit("mod")

    def _codgen_func_call(self, node, scope):
        func_name, args = node[1], node[2]
        arr_key = f"{scope}_{func_name}"
        if arr_key in self.arrays:
            # Acesso a array: NOME(índice)
            self._emit(f"pushg {self._addr(scope, func_name)}")
            self.generate(args[0], scope)
            self._emit("pushi 1", "sub", "loadn")
        else:
            # Chamada a função: passa argumentos, chama, lê retorno
            params = self.functions[func_name]
            for arg in args:
                self.generate(arg, scope)
            for param in reversed(params):
                self._emit(f"storeg {self._addr(func_name, param)}")
            self._emit(f"pusha {func_name}", "call",
                       f"pushg {self._addr(func_name, func_name)}")

    def _codgen_call_stmt(self, node, scope):
        sub_name, args = node[1], node[2]
        params = self.functions[sub_name]
        for arg in args:
            self.generate(arg, scope)
        for param in reversed(params):
            self._emit(f"storeg {self._addr(sub_name, param)}")
        self._emit(f"pusha {sub_name}", "call")

    # Controlo de fluxo

    def _codgen_if(self, node, scope):
        end = self._new_label()
        self.generate(node[1], scope)
        self._emit(f"jz {end}")
        self.generate(node[2], scope)
        self._emit(f"{end}:")

    def _codgen_if_else(self, node, scope):
        false_lbl = self._new_label()
        end_lbl   = self._new_label()
        self.generate(node[1], scope)
        self._emit(f"jz {false_lbl}")
        self.generate(node[2], scope)
        self._emit(f"jump {end_lbl}", f"{false_lbl}:")
        self.generate(node[3], scope)
        self._emit(f"{end_lbl}:")

    def _codgen_goto(self, node, _scope):
        self._emit(f"jump L{node[1]}")

    def _codgen_do(self, node, scope):
        _, lbl, var, start, end = node
        start_lbl = self._new_label()
        end_lbl   = self._new_label()
        self.do_contexts[lbl] = {
            'var': var, 'start_lbl': start_lbl,
            'end_lbl': end_lbl, 'step': 1
        }
        self.generate(start, scope)
        self._emit(f"storeg {self._addr(scope, var)}", f"{start_lbl}:",
                   f"pushg {self._addr(scope, var)}")
        self.generate(end, scope)
        skip = self._new_label()
        self._emit("sup", f"jz {skip}", f"jump {end_lbl}", f"{skip}:")

    def _codgen_do_step(self, node, scope):
        _, lbl, var, start, end, step = node
        start_lbl = self._new_label()
        end_lbl   = self._new_label()
        self.do_contexts[lbl] = {
            'var': var, 'start_lbl': start_lbl,
            'end_lbl': end_lbl, 'step': None,
            'step_expr': step, 'scope': scope
        }
        self.generate(start, scope)
        self._emit(f"storeg {self._addr(scope, var)}", f"{start_lbl}:",
                   f"pushg {self._addr(scope, var)}")
        self.generate(end, scope)
        skip = self._new_label()
        self._emit("sup", f"jz {skip}", f"jump {end_lbl}", f"{skip}:")

    # Labels: WHILE pattern + CONTINUE de DO

    def _codgen_label(self, node, scope):
        lbl_num = node[1]
        stmt    = node[2]
        lbl_str = f"L{lbl_num}:"

        while_match = self._detect_while(lbl_num, stmt)
        if while_match:
            if lbl_str not in self.code:  # só gera uma vez
                cond, body = while_match
                end_lbl = self._new_label()
                self._emit(lbl_str)
                self.generate(cond, scope)
                self._emit(f"jz {end_lbl}")
                self.generate(body, scope)
                self._emit(f"jump L{lbl_num}", f"{end_lbl}:")
            # se já existe, ignora silenciosamente — MAS continua para statements seguintes
        else:
            self._emit(lbl_str)
            self.generate(stmt, scope)
            self._close_do(lbl_num, scope)

    def _detect_while(self, lbl_num: int, stmt) -> tuple | None:
        """
        Deteção do padrão while do Fortran 77:
            N IF (cond) THEN
                ...corpo...
                GOTO N      ← último statement do corpo
            ENDIF
        Devolve (cond, corpo_sem_goto) se detetado, None caso contrário.
        """
        if not isinstance(stmt, tuple) or stmt[0] != 'if':
            return None
        body = stmt[2]
        if not isinstance(body, list) or not body:
            return None
        last = body[-1]
        if isinstance(last, tuple) and last[0] == 'goto' and last[1] == lbl_num:
            return (stmt[1], body[:-1])
        return None

    def _close_do(self, lbl_num: int, scope: str):
        """Fecha um ciclo DO quando encontra o label de destino."""
        if lbl_num not in self.do_contexts:
            return
        ctx = self.do_contexts.pop(lbl_num)
        var = ctx['var']
        self._emit(f"pushg {self._addr(scope, var)}")
        if ctx.get('step_expr') is not None:
            self.generate(ctx['step_expr'], ctx.get('scope', scope))
        else:
            self._emit(f"pushi {ctx.get('step', 1)}")
        self._emit("add", f"storeg {self._addr(scope, var)}",
                   f"jump {ctx['start_lbl']}", f"{ctx['end_lbl']}:")