# semantic.py — Análise Semântica para Fortran 77

# Responsabilidades:
#   - Verificar que todas as variáveis são declaradas antes de serem usadas
#   - Verificar que os labels dos ciclos DO têm CONTINUE correspondente
#   - Verificar que os GOTOs saltam para labels existentes
#   - Verificar chamadas a funções/subrotinas (número de argumentos)


class SemanticError:
    """Representa um erro semântico com localização."""
    def __init__(self, mensagem: str):
        self.mensagem = mensagem

    def __str__(self):
        return self.mensagem


class SemanticAnalyzer:

    def __init__(self):
        self.functions: dict = {}    # nome → {type, num_params}
        self.errors: list[SemanticError] = []
        self._reset_scope()

    # Gestão de escopo

    def _reset_scope(self):
        """Limpa o estado local ao entrar numa nova unidade (programa/função/subrotina)."""
        self.symbol_table: dict  = {}
        self.used_vars:    set   = set()
        self.expected_do_labels:       set = set()
        self.expected_goto_labels:     set = set()
        self.found_continue_labels:    set = set()
        self.found_all_labels:         set = set()

    def _error(self, msg: str):
        self.errors.append(SemanticError(msg))

    # Ponto de entrada público

    def analyze(self, node) -> bool:
        """
        Percorre a AST e verifica a coerência semântica.
        Retorna True se não houver erros.
        """
        self._visit(node)
        return len(self.errors) == 0

    def verify_labels(self):
        """
        Verifica a consistência dos labels após percorrer uma unidade completa.
        Deve ser chamada uma vez por unidade (programa, função, subrotina).
        """
        for label in self.expected_do_labels:
            if label not in self.found_continue_labels:
                self._error(
                    f"O ciclo DO espera o label {label} com CONTINUE, mas não foi encontrado.")

        for label in self.expected_goto_labels:
            if label not in self.found_all_labels:
                self._error(
                    f"GOTO {label}: label não existe no programa.")

    # Visitante recursivo principal
    def _visit(self, node):
        if node is None:
            return
        if isinstance(node, list):
            for n in node:
                self._visit(n)
            return
        if not isinstance(node, tuple):
            return

        kind = node[0]
        visitor = getattr(self, f'_visit_{kind}', self._visit_default)
        visitor(node)

    def _visit_default(self, node):
        """Fallback: visita todos os filhos tuplo/lista."""
        for child in node[1:]:
            self._visit(child)

    # VISITANTES POR TIPO DE NÓ

    def _visit_compilation_unit(self, node):
        # Passagem 1: regista funções e subrotinas primeiro
        for unit in node[1]:
            if unit[0] == 'function':
                self.functions[unit[2]] = {'type': unit[1], 'num_params': len(unit[3])}
            elif unit[0] == 'subroutine':
                self.functions[unit[1]] = {'type': 'VOID', 'num_params': len(unit[2])}
        # Passagem 2: analisa cada unidade e verifica labels no fim
        for unit in node[1]:
            self._visit(unit)
            self.verify_labels()

    def _visit_program(self, node):
        self._reset_scope()
        self._visit(node[2])

    def _visit_function(self, node):
        _, func_type, func_name, params, stmts = node
        self._reset_scope()
        for p in params:
            self.symbol_table[p] = 'UNKNOWN'
        self.symbol_table[func_name] = func_type   # variável de retorno
        self._visit(stmts)

    def _visit_subroutine(self, node):
        _, sub_name, params, stmts = node
        self._reset_scope()
        for p in params:
            self.symbol_table[p] = 'UNKNOWN'
        self._visit(stmts)

    def _visit_declare(self, node):
        _, var_type, items = node
        for item in items:
            if item[0] == 'id':
                self.symbol_table[item[1]] = var_type
            elif item[0] == 'array':
                self.symbol_table[item[1]] = ('ARRAY', var_type, item[2])

    def _visit_assign(self, node):
        _, var_name, expr = node
        if var_name not in self.symbol_table:
            self._error(f"Atribuição a variável não declarada '{var_name}'.")
        self._visit(expr)

    def _visit_assign_array(self, node):
        _, var_name, idx, val = node
        if var_name not in self.symbol_table:
            self._error(f"Atribuição a array não declarado '{var_name}'.")
        elif not (isinstance(self.symbol_table[var_name], tuple)
                  and self.symbol_table[var_name][0] == 'ARRAY'):
            self._error(f"'{var_name}' não é um array.")
        self._visit(idx)
        self._visit(val)

    def _visit_id(self, node):
        var_name = node[1]
        if var_name not in self.symbol_table:
            self._error(f"Variável não declarada '{var_name}'.")

    def _visit_read(self, node):
        var_name = node[1]
        if var_name not in self.symbol_table:
            self._error(f"READ para variável não declarada '{var_name}'.")

    def _visit_read_array(self, node):
        _, var_name, idx = node
        if var_name not in self.symbol_table:
            self._error(f"READ para array não declarado '{var_name}'.")
        elif not (isinstance(self.symbol_table[var_name], tuple)
                  and self.symbol_table[var_name][0] == 'ARRAY'):
            self._error(f"'{var_name}' não é um array (usado como array em READ).")
        self._visit(idx)

    def _visit_print(self, node):
        for item in node[1]:
            if isinstance(item, tuple) and item[0] == 'string':
                pass   # string literal — nada a verificar
            else:
                self._visit(item)

    def _visit_func_call(self, node):
        _, func_name, args = node
        sym = self.symbol_table.get(func_name)
        if isinstance(sym, tuple) and sym[0] == 'ARRAY':
            # Acesso a array disfarçado de chamada a função
            if len(args) != 1:
                self._error(f"Array '{func_name}': índice em falta ou a mais.")
            else:
                self._visit(args[0])
        else:
            if func_name not in self.functions:
                self._error(f"Chamada a função não definida '{func_name}'.")
            elif len(args) != self.functions[func_name]['num_params']:
                esperado = self.functions[func_name]['num_params']
                self._error(
                    f"Função '{func_name}': esperava {esperado} argumentos, recebeu {len(args)}.")
            for arg in args:
                self._visit(arg)

    def _visit_call_stmt(self, node):
        _, sub_name, args = node
        if sub_name not in self.functions:
            self._error(f"CALL a subrotina não definida '{sub_name}'.")
        elif len(args) != self.functions[sub_name]['num_params']:
            esperado = self.functions[sub_name]['num_params']
            self._error(
                f"Subrotina '{sub_name}': esperava {esperado} argumentos, recebeu {len(args)}.")
        for arg in args:
            self._visit(arg)

    def _visit_mod_call(self, node):
        self._visit(node[1])
        self._visit(node[2])

    def _visit_do(self, node):
        _, label, var_name, start, end = node
        if var_name not in self.symbol_table:
            self._error(f"Variável de controlo do DO '{var_name}' não declarada.")
        self.expected_do_labels.add(label)
        self._visit(start)
        self._visit(end)

    def _visit_goto(self, node):
        self.expected_goto_labels.add(node[1])

    def _visit_label(self, node):
        _, num, stmt = node
        self.found_all_labels.add(num)
        if stmt[0] == 'continue':
            self.found_continue_labels.add(num)
        self._visit(stmt)

    def _visit_if(self, node):
        self._visit(node[1])
        self._visit(node[2])

    def _visit_if_else(self, node):
        self._visit(node[1])
        self._visit(node[2])
        self._visit(node[3])

    def _visit_binop(self, node):
        self._visit(node[2])
        self._visit(node[3])

    def _visit_not(self, node):
        self._visit(node[1])

    def _visit_uminus(self, node):
        self._visit(node[1])

    # Nós folha sem filhos a visitar
    def _visit_return(self, node):   pass
    def _visit_continue(self, node): pass
    def _visit_number(self, node):   pass
    def _visit_real(self, node):     pass
    def _visit_bool(self, node):     pass
    def _visit_string(self, node):   pass