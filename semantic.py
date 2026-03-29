class SemanticAnalyzer:
    def __init__(self):
        # A nossa Tabela de Símbolos: chave = nome da variável, valor = tipo (INTEGER, REAL, etc.)
        self.symbol_table = {}
        # Lista para guardar os erros
        self.errors = []
        self.expected_do_labels = set()
        self.expected_goto_labels = set()

        self.found_continue_labels = set()
        self.found_all_labels = set()  # TODOS os labels encontrados

    def analyze(self, node):
        """Função recursiva que percorre a AST"""
        if node is None:
            return

        # Se for uma lista de comandos, analisa cada um individualmente
        if isinstance(node, list):
            for n in node:
                self.analyze(n)
            return

        # Se não for um tuplo, não há nada a analisar aqui
        if not isinstance(node, tuple):
            return

        # O primeiro elemento do tuplo diz-nos que tipo de nó estamos a visitar
        node_type = node[0]

        if node_type == 'program':
            # node = ('program', nome, statements)
            # Vamos analisar a lista de statements (comandos)
            self.analyze(node[2])

        elif node_type == 'declare':
            # node = ('declare', tipo, lista_variaveis)
            var_type = node[1]
            var_list = node[2]
            for var in var_list:
                if var in self.symbol_table:
                    self.errors.append(f"Erro Semântico: A variável '{var}' já foi declarada anteriormente.")
                else:
                    self.symbol_table[var] = var_type

        elif node_type == 'assign':
            # node = ('assign', variavel, expressao)
            var_name = node[1]
            if var_name not in self.symbol_table:
                self.errors.append(f"Erro Semântico: Atribuição a variável não declarada '{var_name}'.")
            # Temos de analisar a expressão do lado direito também (pode ter variáveis lá dentro)
            self.analyze(node[2])

        elif node_type == 'id':
            # node = ('id', nome_variavel) -> Usado dentro de contas e expressões
            var_name = node[1]
            if var_name not in self.symbol_table:
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

        elif node_type == 'print':
            self.analyze(node[1])


        elif node_type == 'goto':
            label_esperado = node[1]
            self.expected_goto_labels.add(label_esperado)


        elif node_type == 'do':
            label_esperado = node[1]
            var_name = node[2]
            if var_name not in self.symbol_table:
                self.errors.append(f"Erro Semântico: Variável de controlo do DO '{var_name}' não declarada.")

            self.expected_do_labels.add(label_esperado)
            self.analyze(node[3])
            self.analyze(node[4])


        elif node_type == 'label':
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