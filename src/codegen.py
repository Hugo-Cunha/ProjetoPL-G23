# codegen.py

class CodeGenerator:
    def __init__(self):
        self.code = []
        self.var_addresses = {}
        self.var_count = 0
        self.functions = {}
        self.label_counter = 0
        self.do_contexts = {}
        self.arrays = {}
        self._while_labels_done = set()

    def new_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"

    def get_addr(self, scope, var_name):
        return self.var_addresses[f"{scope}_{var_name}"]

    # PASSAGEM 1: ALOCAÇÃO DE MEMÓRIA
    def scan_memory(self, node, current_scope=''):
        if node is None: return
        if isinstance(node, list):
            for n in node: self.scan_memory(n, current_scope)
            return
        if not isinstance(node, tuple): return

        t = node[0]
        if t == 'compilation_unit':
            # Alocar memória para todas as variáveis globais (variáveis do programa principal)
            for u in node[1]: self.scan_memory(u)

        elif t == 'program':
            # Programa principal: PROGRAM NOME + corpo
            self.scan_memory(node[2], node[1])

        elif t == 'function':
            # Funções: FUNCTION NOME(params) + corpo + return
            func_name, params, stmts = node[2], node[3], node[4]
            self.functions[func_name] = params
            self.var_addresses[f"{func_name}_{func_name}"] = self.var_count
            self.var_count += 1
            for p in params:
                self.var_addresses[f"{func_name}_{p}"] = self.var_count
                self.var_count += 1
            self.scan_memory(stmts, func_name)

        elif t == 'subroutine':
            # Subrotinas: NOME(params) + corpo
            sub_name, params, stmts = node[1], node[2], node[3]
            self.functions[sub_name] = params
            for p in params:
                self.var_addresses[f"{sub_name}_{p}"] = self.var_count
                self.var_count += 1
            self.scan_memory(stmts, sub_name)

        elif t == 'declare':
            # Variáveis declaradas no corpo de um programa, função ou subrotina
            for item in node[2]:
                if item[0] == 'id':
                    key = f"{current_scope}_{item[1]}"
                    if key not in self.var_addresses:
                        self.var_addresses[key] = self.var_count
                        self.var_count += 1
                elif item[0] == 'array':
                    key = f"{current_scope}_{item[1]}"
                    if key not in self.var_addresses:
                        self.var_addresses[key] = self.var_count
                        self.var_count += item[2]
                        self.arrays[key] = item[2]
        elif t in ('if', 'if_else', 'do', 'do_step', 'label'):
            for e in node[1:]: self.scan_memory(e, current_scope)

    # DETEÇÃO DO PADRÃO WHILE
    # labeled IF + GOTO N no fim do corpo → ciclo while estruturado
    def _is_while_pattern(self, label_num, stmt):
        if not isinstance(stmt, tuple) or stmt[0] != 'if':
            return None
        body = stmt[2]
        if not isinstance(body, list) or len(body) == 0:
            return None
        last = body[-1]
        if isinstance(last, tuple) and last[0] == 'goto' and last[1] == label_num:
            return (stmt[1], body[:-1])   # (condição, corpo sem goto)
        return None

    # PASSAGEM 2: GERAÇÃO DE CÓDIGO
    def generate(self, node, current_scope=''):
        if node is None: return
        if isinstance(node, list):
            for n in node: self.generate(n, current_scope)
            return
        if not isinstance(node, tuple): return

        t = node[0]

        if t == 'compilation_unit':
            # Alocar memória para todas as variáveis globais (variáveis do programa principal)
            for _ in range(self.var_count):
                self.code.append("pushi 0")

            program_node   = next((u for u in node[1] if u[0] == 'program'), None)
            function_nodes = [u for u in node[1] if u[0] in ('function', 'subroutine')]

            self.code.append("start")
            for arr_name, size in self.arrays.items():
                addr = self.var_addresses[arr_name]
                self.code.append(f"alloc {size}")
                self.code.append(f"storeg {addr}")

            self.generate(program_node)
            self.code.append("stop")
            for f in function_nodes:
                self.generate(f)

        elif t == 'program':
            # Programa principal: PROGRAM NOME + corpo
            self.generate(node[2], node[1])

        elif t == 'function':
            # Funções: FUNCTION NOME(params) + corpo + return
            func_name = node[2]
            self.code.append(f"{func_name}:")
            self.generate(node[4], func_name)
            self.code.append("return")

        elif t == 'subroutine':
            # Subrotinas: NOME(params) + corpo + return
            sub_name = node[1]
            self.code.append(f"{sub_name}:")
            self.generate(node[3], sub_name)
            self.code.append("return")

        elif t == 'func_call':
            # Chamadas a funções: NOME(args)
            func_name, args = node[1], node[2]
            arr_key = f"{current_scope}_{func_name}"
            if arr_key in self.arrays:
                # Acesso a array: NOME(índice)
                base_addr = self.get_addr(current_scope, func_name)
                self.code.append(f"pushg {base_addr}")
                self.generate(args[0], current_scope)
                self.code.append("pushi 1")
                self.code.append("sub")
                self.code.append("loadn")
            else:
                params = self.functions[func_name]
                for arg in args:
                    self.generate(arg, current_scope)
                for param in reversed(params):
                    self.code.append(f"storeg {self.get_addr(func_name, param)}")
                self.code.append(f"pusha {func_name}")
                self.code.append("call")
                self.code.append(f"pushg {self.get_addr(func_name, func_name)}")

        elif t == 'call_stmt':
            # Chamadas a subrotinas: CALL NOME(args)
            sub_name, args = node[1], node[2]
            params = self.functions[sub_name]
            for arg in args:
                self.generate(arg, current_scope)
            for param in reversed(params):
                self.code.append(f"storeg {self.get_addr(sub_name, param)}")
            self.code.append(f"pusha {sub_name}")
            self.code.append("call")

        elif t == 'return':
            # Retorno de função: gera código para a expressão de retorno e depois retorna
            self.code.append("return")

        elif t == 'mod_call':
            # Chamadas a funções intrínsecas: MOD(expr1, expr2)
            self.generate(node[1], current_scope)
            self.generate(node[2], current_scope)
            self.code.append("mod")

        elif t == 'assign':
            # Atribuição a variável simples: VAR = valor
            self.generate(node[2], current_scope)
            self.code.append(f"storeg {self.get_addr(current_scope, node[1])}")

        elif t == 'assign_array':
            # Atribuição a array: NOME(índice) = valor
            var_name, idx_expr, val_expr = node[1], node[2], node[3]
            base = self.get_addr(current_scope, var_name)
            self.code.append(f"pushg {base}")
            self.generate(idx_expr, current_scope)
            self.code.append("pushi 1")
            self.code.append("sub")
            self.generate(val_expr, current_scope)
            self.code.append("storen")

        elif t == 'id':
            # Acesso a variável simples: pushg endereço
            self.code.append(f"pushg {self.get_addr(current_scope, node[1])}")

        elif t == 'number':
            # Valores inteiros: pushi valor
            self.code.append(f"pushi {node[1]}")

        elif t == 'real':
            # Valores reais: pushf valor
            self.code.append(f"pushf {node[1]}")

        elif t == 'uminus':
            # Gerar código para o valor interno e depois multiplicar por -1
            inner = node[1]
            if inner[0] == 'number':
                self.code.append(f"pushi {-inner[1]}")
            elif inner[0] == 'real':
                self.code.append(f"pushf {-inner[1]}")
            else:
                self.generate(inner, current_scope)
                self.code.append("pushi -1")
                self.code.append("mul")

        elif t == 'bool':
            # Valores booleanos: .TRUE. → 1, .FALSE. → 0
            self.code.append("pushi 1" if node[1] == '.TRUE.' else "pushi 0")

        elif t == 'binop':
            # Gerar código para os operandos (sempre na ordem esquerda → direita)
            self.generate(node[2], current_scope)
            self.generate(node[3], current_scope)
            op = node[1]
            ops = {
                '+': 'add', '-': 'sub', '*': 'mul', '/': 'div',
                '.EQ.': 'equal', '.GT.': 'sup', '.GE.': 'supeq',
                '.LT.': 'inf', '.LE.': 'infeq',
            }
            if op in ops:
                self.code.append(ops[op])
            elif op == '.NE.':
                self.code.append("equal")
                self.code.append("pushi 0")
                self.code.append("equal")
            elif op == '.AND.':
                self.code.append("mul")
            elif op == '.OR.':
                self.code.append("add")
                self.code.append("pushi 0")
                self.code.append("sup")

        elif t == 'not':
            # NOT x → x == 0
            self.generate(node[1], current_scope)
            self.code.append("pushi 0")
            self.code.append("equal")

        elif t == 'print':
            # node[1] é uma lista de itens a imprimir (strings literais ou expressões)
            for item in node[1]:
                if isinstance(item, tuple) and item[0] == 'string':
                    # String literal — pushs + writes
                    # Escapar aspas duplas que possam estar no texto
                    txt = item[1].replace('"', '\\"')
                    self.code.append(f'pushs "{txt}"')
                    self.code.append("writes")
                elif isinstance(item, tuple) and item[0] == 'real':
                    self.generate(item, current_scope)
                    self.code.append("writef")
                else:
                    # Expressão numérica/lógica → writei
                    self.generate(item, current_scope)
                    self.code.append("writei")
            self.code.append("writeln")

        elif t == 'read':
            # Leitura para variável simples: READ *, VAR
            self.code.append("read")
            self.code.append("atoi")
            self.code.append(f"storeg {self.get_addr(current_scope, node[1])}")

        elif t == 'read_array':
            # Leitura para array: NOME(índice)
            var_name, idx_expr = node[1], node[2]
            base = self.get_addr(current_scope, var_name)
            self.code.append(f"pushg {base}")
            self.generate(idx_expr, current_scope)
            self.code.append("pushi 1")
            self.code.append("sub")
            self.code.append("read")
            self.code.append("atoi")
            self.code.append("storen")

        elif t == 'if':
            # IF sem ELSE → if (cond) then stmt ENDIF
            end_lbl = self.new_label()
            self.generate(node[1], current_scope)
            self.code.append(f"jz {end_lbl}")
            self.generate(node[2], current_scope)
            self.code.append(f"{end_lbl}:")

        elif t == 'if_else':
            # IF com ELSE → if (cond) then stmt1 else stmt2 ENDIF
            false_lbl = self.new_label()
            end_lbl   = self.new_label()
            self.generate(node[1], current_scope)
            self.code.append(f"jz {false_lbl}")
            self.generate(node[2], current_scope)
            self.code.append(f"jump {end_lbl}")
            self.code.append(f"{false_lbl}:")
            self.generate(node[3], current_scope)
            self.code.append(f"{end_lbl}:")

        elif t == 'goto':
            self.code.append(f"jump L{node[1]}")

        # LABEL: deteção do padrão WHILE + ciclos DO
        elif t == 'label':
            lbl_num = node[1]
            stmt    = node[2]

            while_match = self._is_while_pattern(lbl_num, stmt)
            if while_match and lbl_num not in self._while_labels_done:
                # Padrão while detetado — gera ciclo estruturado
                self._while_labels_done.add(lbl_num)
                cond, body = while_match
                while_end = self.new_label()

                self.code.append(f"L{lbl_num}:")          # entrada do while
                self.generate(cond, current_scope)          # avalia condição
                self.code.append(f"jz {while_end}")         # sai se falsa
                self.generate(body, current_scope)           # corpo sem o GOTO
                self.code.append(f"jump L{lbl_num}")        # volta ao início
                self.code.append(f"{while_end}:")

            elif while_match and lbl_num in self._while_labels_done:
                pass  # ignorar silenciosamente

            else:
                # Label normal (CONTINUE de DO loop ou label de GOTO simples)
                self.code.append(f"L{lbl_num}:")
                self.generate(stmt, current_scope)

                # Fechar ciclo DO se este label for o destino
                if lbl_num in self.do_contexts:
                    ctx = self.do_contexts.pop(lbl_num)
                    var = ctx['var']
                    step_expr = ctx.get('step_expr')
                    step_val  = ctx.get('step', 1)

                    self.code.append(f"pushg {self.get_addr(current_scope, var)}")
                    if step_expr is not None:
                        self.generate(step_expr, ctx.get('current_scope', current_scope))
                    else:
                        self.code.append(f"pushi {step_val}")
                    self.code.append("add")
                    self.code.append(f"storeg {self.get_addr(current_scope, var)}")
                    self.code.append(f"jump {ctx['start_lbl']}")
                    self.code.append(f"{ctx['end_lbl']}:")

        elif t == 'do':
            lbl_num, var_name = node[1], node[2]
            start_expr, end_expr = node[3], node[4]
            start_lbl = self.new_label()
            end_lbl   = self.new_label()

            self.do_contexts[lbl_num] = {
                'var': var_name, 'start_lbl': start_lbl,
                'end_lbl': end_lbl, 'step': 1
            }
            self.generate(start_expr, current_scope)
            self.code.append(f"storeg {self.get_addr(current_scope, var_name)}")
            self.code.append(f"{start_lbl}:")
            self.code.append(f"pushg {self.get_addr(current_scope, var_name)}")
            self.generate(end_expr, current_scope)
            self.code.append("sup")
            skip_lbl = self.new_label()
            self.code.append(f"jz {skip_lbl}")
            self.code.append(f"jump {end_lbl}")
            self.code.append(f"{skip_lbl}:")

        elif t == 'do_step':
            lbl_num, var_name = node[1], node[2]
            start_expr, end_expr, step_expr = node[3], node[4], node[5]
            start_lbl = self.new_label()
            end_lbl   = self.new_label()

            self.do_contexts[lbl_num] = {
                'var': var_name, 'start_lbl': start_lbl,
                'end_lbl': end_lbl, 'step': None,
                'step_expr': step_expr, 'current_scope': current_scope
            }
            self.generate(start_expr, current_scope)
            self.code.append(f"storeg {self.get_addr(current_scope, var_name)}")
            self.code.append(f"{start_lbl}:")
            self.code.append(f"pushg {self.get_addr(current_scope, var_name)}")
            self.generate(end_expr, current_scope)
            self.code.append("sup")
            skip_lbl = self.new_label()
            self.code.append(f"jz {skip_lbl}")
            self.code.append(f"jump {end_lbl}")
            self.code.append(f"{skip_lbl}:")

        elif t == 'continue':
            pass

        elif t == 'string':
            # Nó string usado fora de print (não devia acontecer, mas por segurança)
            txt = node[1].replace('"', '\\"')
            self.code.append(f'pushs "{txt}"')