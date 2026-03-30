class SemanticAnalyzer:
    def __init__(self):
        self.functions = {}
        self.errors = []
        self.reset_local_scope()

    def reset_local_scope(self):
        """Limpa as variáveis e os labels locais ao entrar num novo bloco de código."""
        self.symbol_table = {}
        self.used_vars = set()
        self.expected_do_labels = set()
        self.expected_goto_labels = set()
        self.found_continue_labels = set()
        self.found_all_labels = set()

    def analyze(self, node):
        """Função recursiva que percorre a AST"""
        if node is None:
            return

        if isinstance(node, list):
            for n in node:
                self.analyze(n)
            return

        if not isinstance(node, tuple):
            return

        node_type = node[0]

        if node_type == 'compilation_unit':
            # Passagem 1: regista todas as funções/subrotinas antes de analisar o corpo
            for unit in node[1]:
                if unit[0] == 'function':
                    func_type, func_name, params = unit[1], unit[2], unit[3]
                    self.functions[func_name] = {'type': func_type, 'num_params': len(params)}
                elif unit[0] == 'subroutine':
                    self.functions[unit[1]] = {'type': 'VOID', 'num_params': len(unit[2])}
            # Passagem 2: analisa cada unidade individualmente
            for unit in node[1]:
                self.analyze(unit)
                self.verify_labels()

        elif node_type == 'program':
            # node = ('program', nome_programa, comandos)
            self.reset_local_scope()
            self.analyze(node[2])

        elif node_type == 'function':
            # node = ('function', tipo, nome_funcao, parametros, comandos)
            func_type, func_name, params, statements = node[1], node[2], node[3], node[4]
            self.reset_local_scope()
            for param in params:
                self.symbol_table[param] = 'UNKNOWN'
            # No Fortran 77 o nome da função é também a variável de retorno
            self.symbol_table[func_name] = func_type
            self.analyze(statements)

        elif node_type == 'subroutine':
            # node = ('subroutine', nome, parametros, comandos)
            sub_name, params, statements = node[1], node[2], node[3]
            self.reset_local_scope()
            for param in params:
                self.symbol_table[param] = 'UNKNOWN'
            self.analyze(statements)

        elif node_type == 'func_call':
            # node = ('func_call', nome_funcao, lista_argumentos)
            func_name, args = node[1], node[2]

            # Se o nome existe na tabela de símbolos como ARRAY, é um acesso a array
            scoped_key = func_name
            if scoped_key in self.symbol_table and isinstance(self.symbol_table[scoped_key], tuple) and self.symbol_table[scoped_key][0] == 'ARRAY':
                # É um acesso a array — verifica só o índice
                if len(args) != 1:
                    self.errors.append(f"Erro Semântico: Acesso ao array '{func_name}' com número errado de índices.")
                else:
                    self.analyze(args[0])
            else:
                # É uma chamada a função real
                if func_name not in self.functions:
                    self.errors.append(f"Erro Semântico: Chamada a função não definida '{func_name}'.")
                elif len(args) != self.functions[func_name]['num_params']:
                    self.errors.append(
                        f"Erro Semântico: A função '{func_name}' esperava {self.functions[func_name]['num_params']} argumentos, mas recebeu {len(args)}.")
                for arg in args:
                    self.analyze(arg)

        elif node_type == 'mod_call':
            # node = ('mod_call', expressao_a, expressao_b)
            self.analyze(node[1])
            self.analyze(node[2])

        elif node_type == 'call_stmt':
            # node = ('call_stmt', nome_subrotina, argumentos)
            sub_name, args = node[1], node[2]
            if sub_name not in self.functions:
                self.errors.append(f"Erro Semântico: CALL a subrotina não definida '{sub_name}'.")
            elif len(args) != self.functions[sub_name]['num_params']:
                self.errors.append(
                    f"Erro Semântico: A subrotina '{sub_name}' esperava {self.functions[sub_name]['num_params']} argumentos.")
            for arg in args:
                self.analyze(arg)

        elif node_type == 'return':
            pass

        elif node_type == 'declare':
            # node = ('declare', tipo, lista_variaveis)
            var_type = node[1]
            for item in node[2]:
                if item[0] == 'id':
                    var_name = item[1]
                    if var_name in self.functions:
                        # Em Fortran é válido declarar o nome da função dentro dela própria, por isso só avisamos se for noutra unidade
                        pass
                    self.symbol_table[var_name] = var_type
                elif item[0] == 'array':
                    var_name, size = item[1], item[2]
                    self.symbol_table[var_name] = ('ARRAY', var_type, size)

        elif node_type == 'assign':
            # node = ('assign', variavel, expressao)
            var_name = node[1]
            if var_name not in self.symbol_table:
                self.used_vars.add(var_name)
                self.errors.append(f"Erro Semântico: Atribuição a variável não declarada '{var_name}'.")
            self.analyze(node[2])

        elif node_type == 'assign_array':
            # node = ('assign_array', nome_array, indice, valor)
            var_name, index_expr, value_expr = node[1], node[2], node[3]
            if var_name not in self.symbol_table:
                self.errors.append(f"Erro Semântico: Atribuição a array não declarado '{var_name}'.")
            elif not (isinstance(self.symbol_table[var_name], tuple) and self.symbol_table[var_name][0] == 'ARRAY'):
                self.errors.append(f"Erro Semântico: '{var_name}' não é um array.")
            self.analyze(index_expr)
            self.analyze(value_expr)

        elif node_type == 'read_array':
            # node = ('read_array', nome_array, indice)
            var_name, index_expr = node[1], node[2]
            if var_name not in self.symbol_table:
                self.errors.append(f"Erro Semântico: READ para array não declarado '{var_name}'.")
            elif not (isinstance(self.symbol_table[var_name], tuple) and self.symbol_table[var_name][0] == 'ARRAY'):
                self.errors.append(f"Erro Semântico: '{var_name}' não é um array (usado como array em READ).")
            self.analyze(index_expr)

        elif node_type == 'id':
            # node = ('id', nome_variavel)
            var_name = node[1]
            if var_name not in self.symbol_table:
                self.used_vars.add(var_name)
                self.errors.append(f"Erro Semântico: Uso de variável não declarada '{var_name}'.")

        elif node_type == 'read':
            # node = ('read', nome_variavel)
            var_name = node[1]
            if var_name not in self.symbol_table:
                self.errors.append(f"Erro Semântico: Tentativa de ler para variável não declarada '{var_name}'.")

        elif node_type == 'binop':
            # node = ('binop', operador, lado_esquerdo, lado_direito)
            self.analyze(node[2])
            self.analyze(node[3])

        elif node_type == 'not':
            # node = ('not', expressao)
            self.analyze(node[1])

        elif node_type == 'print':
            # node = ('print', lista_itens)
            # FIX: strings são agora nós ('string', valor) — não analisar como expressão
            for item in node[1]:
                if isinstance(item, tuple) and item[0] == 'string':
                    pass  # string literal, nada a verificar semanticamente
                else:
                    self.analyze(item)

        elif node_type == 'if':
            # node = ('if', condição, bloco_verdadeiro)
            self.analyze(node[1])  # condição
            self.analyze(node[2])  # bloco verdadeiro

        elif node_type == 'if_else':
            # node = ('if_else', condição, bloco_verdadeiro, bloco_falso)
            self.analyze(node[1])  # condição
            self.analyze(node[2])  # bloco verdadeiro
            self.analyze(node[3])  # bloco falso

        elif node_type == 'do':
            # node = ('do', label_esperado, var_name, inicio, fim)
            label_esperado = node[1]
            var_name = node[2]
            if var_name not in self.symbol_table:
                self.errors.append(f"Erro Semântico: Variável de controlo do DO '{var_name}' não declarada.")
            self.expected_do_labels.add(label_esperado)
            self.analyze(node[3])  # expressão de início
            self.analyze(node[4])  # expressão de fim

        elif node_type == 'goto':
            # node = ('goto', label_num)
            self.expected_goto_labels.add(node[1])

        elif node_type == 'label':
            # node = ('label', num_label, statement)
            num_label = node[1]
            statement = node[2]
            self.found_all_labels.add(num_label)

            if statement[0] == 'continue':
                self.found_continue_labels.add(num_label)

            self.analyze(statement)

    def verify_labels(self):
        for label in self.expected_do_labels:
            if label not in self.found_continue_labels:
                self.errors.append(
                    f"Erro Semântico: O ciclo DO exige o label {label} associado a um CONTINUE, mas ele não foi encontrado.")

        for label in self.expected_goto_labels:
            if label not in self.found_all_labels:
                self.errors.append(
                    f"Erro Semântico: O comando GOTO tenta saltar para o label {label}, mas essa linha não existe.")

    def report_warnings(self, scope_name):
        """Imprime avisos sobre variáveis declaradas mas nunca utilizadas."""
        for var in self.symbol_table:
            if var != scope_name and var not in self.used_vars and self.symbol_table[var] != 'UNKNOWN':
                print(f" [!] Warning: Variável '{var}' no bloco '{scope_name}' declarada mas nunca utilizada.")