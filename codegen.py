# codegen.py

class CodeGenerator:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.code = []
        self.var_addresses = {}
        self.var_count = 0
        self.label_counter = 0 # Para gerir os saltos e ciclos (cria labels únicas como L1, L2...)
        self.do_contexts = {} # Guarda o contexto dos ciclos DO para sabermos o que fazer quando lermos um CONTINUE

    def new_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"

    def generate(self, node):
        if node is None: return

        # Se for uma lista de comandos, analisa cada um pela ordem em que aparecem
        if isinstance(node, list):
            for n in node:
                self.generate(n)
            return

        if not isinstance(node, tuple): return

        node_type = node[0]

        if node_type == 'program':
            # 1. RESERVAR MEMÓRIA PARA AS VARIÁVEIS GLOBAIS
            for var in self.symbol_table:
                self.var_addresses[var] = self.var_count
                self.var_count += 1
                self.code.append("pushi 0")  # Aloca espaço na memória da VM

            # 2. INICIAR A EXECUÇÃO E PROCESSAR OS COMANDOS
            self.code.append("start")
            self.generate(node[2])
            self.code.append("stop")

        elif node_type == 'declare':
            pass

        elif node_type == 'number':
            self.code.append(f"pushi {node[1]}")  # Põe o número na pilha

        elif node_type == 'id':
            # Põe o valor da variável na pilha
            self.code.append(f"pushg {self.var_addresses[node[1]]}")

        elif node_type == 'assign':
            # node = ('assign', variavel, expressao)
            self.generate(node[2])  # Avalia a expressão matemática toda
            # O resultado vai ficar no topo da pilha. Guardamos na variável.
            self.code.append(f"storeg {self.var_addresses[node[1]]}")

        elif node_type == 'binop':
            op = node[1]
            self.generate(node[2])  # Lado esquerdo da conta
            self.generate(node[3])  # Lado direito da conta

            if op == '+':
                self.code.append("add")
            elif op == '-':
                self.code.append("sub")
            elif op == '*':
                self.code.append("mul")
            elif op == '/':
                self.code.append("div")

        elif node_type == 'read':
            # A EWVM recebe o input como texto, logo temos de ler (read) e converter para inteiro (atoi)
            self.code.append("read")
            self.code.append("atoi")
            self.code.append(f"storeg {self.var_addresses[node[1]]}")

        elif node_type == 'print':
            if isinstance(node[1], str) and node[1].startswith("'"):  # Se for texto literal
                txt = node[1].replace("'", '"')  # A VM prefere aspas duplas
                self.code.append(f"pushs {txt}")
                self.code.append("writes")
            else:  # Se for para imprimir o resultado de uma conta ou variável
                self.generate(node[1])
                self.code.append("writei")
            self.code.append("writeln")  # Pula linha para ficar bonito no output

        # ==========================================
        # A MAGIA DOS CICLOS DO (Lógica Avançada)
        # ==========================================
        elif node_type == 'do':
            # node = ('do', label_num, variavel, inicio, fim)
            label_num, var_name = node[1], node[2]

            # 1. Atribui o valor de 'inicio' à variável (ex: I = 1)
            self.generate(node[3])
            self.code.append(f"storeg {self.var_addresses[var_name]}")

            # 2. Prepara os Labels da VM
            start_label = self.new_label()
            end_label = self.new_label()

            # Guarda as indicações para quando encontrarmos o CONTINUE mais à frente
            self.do_contexts[label_num] = {
                'var': var_name, 'end_exp': node[4],
                'start_label': start_label, 'end_label': end_label
            }

            # 3. Marca o Ponto de Partida do ciclo
            self.code.append(f"{start_label}:")

            # 4. Condição: Põe a variável (I) e o limite (N) na pilha. Compara se (I <= N)
            self.code.append(f"pushg {self.var_addresses[var_name]}")
            self.generate(node[4])
            self.code.append("infeq")  # 'infeq' = Inferior ou Igual
            self.code.append(f"jz {end_label}")  # Se a comparação for Falsa (0), salta fora!

        elif node_type == 'label':
            # node = ('label', numero, comando)
            label_num, statement = node[1], node[2]

            # Se a linha acabar com CONTINUE, este é o momento de fazer a variável andar (I = I + 1) e repetir!
            if statement[0] == 'continue':
                ctx = self.do_contexts[label_num]
                var_name = ctx['var']

                # 1. Incrementa a variável do ciclo
                self.code.append(f"pushg {self.var_addresses[var_name]}")
                self.code.append("pushi 1")
                self.code.append("add")
                self.code.append(f"storeg {self.var_addresses[var_name]}")

                # 2. Salta de volta para a verificação do ciclo
                self.code.append(f"jump {ctx['start_label']}")

                # 3. Marca aqui o destino final de paragem (para quando o ciclo terminar)
                self.code.append(f"{ctx['end_label']}:")
            else:
                self.generate(statement)