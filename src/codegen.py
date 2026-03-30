# codegen.py

class CodeGenerator:
    def __init__(self):
        self.code = []
        self.var_addresses = {}
        self.var_count = 0
        self.functions = {}  # Guarda os parâmetros de cada função
        self.label_counter = 0
        self.do_contexts = {}
        self.arrays = {}
        self._while_labels_emitted = set()

    def new_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"

    def get_addr(self, scope, var_name):
        """Devolve o endereço de memória de uma variável dentro de um escopo."""
        return self.var_addresses[f"{scope}_{var_name}"]

    # PASSAGEM 1: ALOCAÇÃO DE MEMÓRIA GLOBAL
    def scan_memory(self, node, current_scope=''):
        """Percorre a AST e regista TODAS as variáveis de todos os blocos."""
        if node is None: return
        if isinstance(node, list):
            for n in node: self.scan_memory(n, current_scope)
            return
        if not isinstance(node, tuple): return

        node_type = node[0]

        if node_type == 'compilation_unit':
            for unit in node[1]: self.scan_memory(unit)
        elif node_type == 'program':
            self.scan_memory(node[2], node[1])
        elif node_type == 'function':
            func_name, params, statements = node[2], node[3], node[4]
            self.functions[func_name] = params

            # A variável de retorno tem o mesmo nome da função!
            self.var_addresses[f"{func_name}_{func_name}"] = self.var_count
            self.var_count += 1

            # Regista os parâmetros
            for param in params:
                self.var_addresses[f"{func_name}_{param}"] = self.var_count
                self.var_count += 1

            self.scan_memory(statements, func_name)
        elif node_type == 'subroutine':
            sub_name, params, statements = node[1], node[2], node[3]
            self.functions[sub_name] = params
            for param in params:
                self.var_addresses[f"{sub_name}_{param}"] = self.var_count
                self.var_count += 1
            self.scan_memory(statements, sub_name)

        elif node_type == 'declare':
            for item in node[2]:
                if item[0] == 'id':
                    self.var_addresses[f"{current_scope}_{item[1]}"] = self.var_count
                    self.var_count += 1
                elif item[0] == 'array':
                    self.var_addresses[f"{current_scope}_{item[1]}"] = self.var_count
                    self.var_count += item[2]  # Aloca N espaços na memória!
                    self.arrays[f"{current_scope}_{item[1]}"] = item[2]

        elif node_type in ('if', 'if_else', 'do', 'label'):
            # Procura variáveis dentro dos blocos internos
            for element in node[1:]:
                self.scan_memory(element, current_scope)

    def _is_while_pattern(self, label_num, stmt):
        """
        Verifica se um nó 'label' representa o padrão while do Fortran 77:
            N IF (cond) THEN
                ...corpo...
                GOTO N
            ENDIF
        Se sim, devolve (cond, corpo_sem_goto). Caso contrário, devolve None.
        """
        if stmt[0] not in ('if', 'if_else'):
            return None

        # Só tratamos IF sem ELSE como while (IF com ELSE é outra coisa)
        if stmt[0] == 'if_else':
            return None

        cond = stmt[1]
        body = stmt[2]  # lista de statements dentro do IF

        if not isinstance(body, list) or len(body) == 0:
            return None

        last = body[-1]
        # O último statement do corpo tem de ser GOTO N (o mesmo label)
        if last[0] == 'goto' and last[1] == label_num:
            body_sem_goto = body[:-1]
            return (cond, body_sem_goto)

        return None

    # PASSAGEM 2: GERAÇÃO DE CÓDIGO
    def generate(self, node, current_scope=''):
        if node is None: return
        if isinstance(node, list):
            for n in node: self.generate(n, current_scope)
            return
        if not isinstance(node, tuple): return

        node_type = node[0]

        if node_type == 'compilation_unit':
            # Aloca espaço físico na VM para TODAS as variáveis do programa e funções
            for _ in range(self.var_count):
                self.code.append("pushi 0")

            # Encontra os blocos
            program_node = next((u for u in node[1] if u[0] == 'program'), None)
            function_nodes = [u for u in node[1] if u[0] in ('function', 'subroutine')]

            # Executa o programa principal e FORÇA a paragem
            self.code.append("start")

            for arr_name, size in self.arrays.items():
                addr = self.var_addresses[arr_name]
                self.code.append(f"alloc {size}")
                self.code.append(f"storeg {addr}")

            self.generate(program_node)
            self.code.append("stop")

            # 4. Coloca o código das funções cá em baixo (só correm quando chamadas)
            for f in function_nodes:
                self.generate(f)

        elif node_type == 'program':
            # Nó: ('program', nome_programa, comandos)
            self.generate(node[2], node[1])  # Analisa os statements do programa

        elif node_type == 'function':
            # Nó: ('function', tipo, nome_funcao, parametros, comandos)
            func_name = node[2]
            self.code.append(f"{func_name}:")  # Ponto de entrada da função
            self.generate(node[4], func_name)
            self.code.append("return")  # Retorna ao ponto onde foi chamada

        elif node_type == 'subroutine':
            # Nó: ('subroutine', nome, parametros, comandos)
            sub_name = node[1]
            self.code.append(f"{sub_name}:")  # Ponto de entrada da sub-rotina
            self.generate(node[3], sub_name)
            self.code.append("return")  # Retorna ao ponto onde foi chamada

        elif node_type == 'func_call':
            # Nó: ('func_call', nome_funcao, lista_argumentos)
            func_name, args = node[1], node[2]
            if f"{current_scope}_{func_name}" in self.arrays:
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

        elif node_type == 'call_stmt':
            # Nó: ('call_stmt', nome_subrotina, argumentos)
            sub_name, args = node[1], node[2]
            params = self.functions[sub_name]
            for arg in args:
                self.generate(arg, current_scope)
            for param in reversed(params):
                self.code.append(f"storeg {self.get_addr(sub_name, param)}")
            self.code.append(f"pusha {sub_name}")
            self.code.append("call")

        elif node_type == 'return':
            # Nó: ('return', expressão_retorno)
            self.code.append("return")

        elif node_type == 'mod_call':
            # Nó: ('mod_call', nome_modulo, nome_funcao, lista_argumentos)
            self.generate(node[1], current_scope)
            self.generate(node[2], current_scope)
            self.code.append("mod")

        elif node_type == 'assign':
            # Nó: ('assign', nome_variavel, expressão)
            self.generate(node[2], current_scope)
            self.code.append(f"storeg {self.get_addr(current_scope, node[1])}")

        elif node_type == 'id':
            # Nó: ('id', nome_variavel)
            self.code.append(f"pushg {self.get_addr(current_scope, node[1])}")

        elif node_type == 'number':
            # Nó: ('number', valor)
            self.code.append(f"pushi {node[1]}")

        elif node_type == 'real':
            self.code.append(f"pushf {node[1]}")

        elif node_type == 'uminus':
            inner = node[1]
            # Otimização inline: se o filho é uma constante, já gera o número negativo diretamente
            if inner[0] == 'number':
                self.code.append(f"pushi {-inner[1]}")
            else:
                self.generate(inner, current_scope)
                self.code.append("pushi -1")
                self.code.append("mul")

        elif node_type == 'binop':
            # Nó: ('binop', operador, lado_esquerdo, lado_direito)
            self.generate(node[2], current_scope)
            self.generate(node[3], current_scope)
            op = node[1]
            if op == '+':
                self.code.append("add")
            elif op == '-':
                self.code.append("sub")
            elif op == '*':
                self.code.append("mul")
            elif op == '/':
                self.code.append("div")
            elif op == '.EQ.':
                self.code.append("equal")
            elif op == '.GT.':
                self.code.append("sup")
            elif op == '.GE.':
                self.code.append("supeq")
            elif op == '.LT.':
                self.code.append("inf")
            elif op == '.LE.':
                self.code.append("infeq")
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

        elif node_type == 'print':
            # Nó: ('print', lista_argumentos)
            for item in node[1]:
                if isinstance(item, str) and item.startswith("'"):
                    txt = item.replace("'", '"')
                    self.code.append(f"pushs {txt}")
                    self.code.append("writes")
                else:
                    self.generate(item, current_scope)
                    self.code.append("writei")
                # Só depois de imprimir tudo na mesma linha é que manda o 'enter'
            self.code.append("writeln")

        elif node_type == 'read':
            # Nó: ('read', variavel)
            # READ *, NUM
            self.code.append("read")
            self.code.append("atoi")
            self.code.append(f"storeg {self.get_addr(current_scope, node[1])}")

        elif node_type == 'read_array':
            #Nó: ('read_array', nome_array, indice)
            # READ *, NUMS(I)
            var_name, index_expr = node[1], node[2]
            base_addr = self.get_addr(current_scope, var_name)

            self.code.append(f"pushg {base_addr}")
            self.generate(index_expr, current_scope)
            self.code.append("pushi 1")
            self.code.append("sub")
            self.code.append("read")
            self.code.append("atoi")
            self.code.append("storen")

        elif node_type == 'assign_array':
            # Nó: ('assign_array', nome_array, indice, valor)
            # Atribuição a um elemento do array: ex: NUMS(I) = 5 TESTE4
            var_name, index_expr, value_expr = node[1], node[2], node[3]
            base_addr = self.get_addr(current_scope, var_name)

            self.code.append(f"pushg {base_addr}")
            self.generate(index_expr, current_scope)
            self.code.append("pushi 1")
            self.code.append("sub")
            self.generate(value_expr, current_scope)
            self.code.append("storen")

        elif node_type == 'bool':
            # Nó: ('bool', valor) onde valor é '.TRUE.' ou '.FALSE.'
            # Verdadeiro é 1, Falso é 0
            if node[1] == '.TRUE.':
                self.code.append("pushi 1")
            else:
                self.code.append("pushi 0")

        elif node_type == 'if':
            # Nó: ('if', condicao, bloco_verdadeiro)
            end_label = self.new_label()
            self.generate(node[1], current_scope)  # Avalia a condição
            self.code.append(f"jz {end_label}")  # Se for falsa (0), salta o bloco
            self.generate(node[2], current_scope)  # Executa o bloco se for verdadeira
            self.code.append(f"{end_label}:")  # Etiqueta de saída

        elif node_type == 'if_else':
            # Nó: ('if_else', condicao, verdadeiro, falso)
            false_label = self.new_label()
            end_label = self.new_label()

            self.generate(node[1], current_scope)
            self.code.append(f"jz {false_label}")
            self.generate(node[2], current_scope)  # Bloco Verdadeiro
            self.code.append(f"jump {end_label}")

            self.code.append(f"{false_label}:")
            self.generate(node[3], current_scope)  # Bloco Falso
            self.code.append(f"{end_label}:")

        elif node_type == 'not':
            # Nó: ('not', expressão)
            self.generate(node[1], current_scope)
            self.code.append("pushi 0")
            self.code.append("equal")

        elif node_type == 'goto':
            # GOTO 20
            # Nó: ('goto', numero_label)
            self.code.append(f"jump L{node[1]}")

        elif node_type == 'label':
            # Nó: ('label', numero, comando)
            lbl_num = node[1]
            stmt = node[2]

            self.code.append(f"L{lbl_num}:")
            self.generate(stmt, current_scope)

            # --- CICLO PADRAO WHILE ---
            while_match = self._is_while_pattern(lbl_num, stmt)
            if while_match and lbl_num not in self._while_labels_emitted:
                cond, body = while_match
                self._while_labels_emitted.add(lbl_num)
                while_start = f"L{lbl_num}"
                while_end = self.new_label()

                self.code.append(f"{while_start}:")
                self.generate(cond, current_scope)
                self.code.append(f"jz {while_end}")
                self.generate(body, current_scope)
                self.code.append(f"jump {while_start}")
                self.code.append(f"{while_end}:")
            elif while_match and lbl_num in self._while_labels_emitted:
                pass

            else:
                # Comportamento normal: emite o label e o statement
                self.code.append(f"L{lbl_num}:")
                self.generate(stmt, current_scope)

                # Se há um ciclo DO à espera deste label, fecha-o aqui
                if lbl_num in self.do_contexts:
                    ctx = self.do_contexts.pop(lbl_num)
                    # Incrementa a variável de controlo
                    self.code.append(f"pushg {self.get_addr(current_scope, ctx['var'])}")
                    step = ctx.get('step', 1)
                    self.code.append(f"pushi {step}")
                    self.code.append("add")
                    self.code.append(f"storeg {self.get_addr(current_scope, ctx['var'])}")
                    # Volta ao início do ciclo
                    self.code.append(f"jump {ctx['start_lbl']}")
                    self.code.append(f"{ctx['end_lbl']}:")

        elif node_type == 'do':
            # Nó: ('do', label_destino, variavel, inicio, fim)
            lbl_num = node[1]
            var_name = node[2]
            start_expr = node[3]
            end_expr = node[4]

            start_lbl = self.new_label()
            end_lbl = self.new_label()

            # Guarda o contexto para quando encontrarmos o label de fecho
            self.do_contexts[lbl_num] = {
                'var': var_name,
                'start_lbl': start_lbl,
                'end_lbl': end_lbl
            }

            # Atribui o valor inicial à variável do DO
            self.generate(start_expr, current_scope)
            self.code.append(f"storeg {self.get_addr(current_scope, var_name)}")
            self.code.append(f"{start_lbl}:")
            # Condição de paragem (variavel > fim)
            self.code.append(f"pushg {self.get_addr(current_scope, var_name)}")
            self.generate(end_expr, current_scope)
            self.code.append("sup")
            skip_lbl = self.new_label()
            self.code.append(f"jz {skip_lbl}")  # Se for 0 (var <= fim), salta a instrução de paragem
            self.code.append(f"jump {end_lbl}")  # Se for 1, o ciclo acabou!
            self.code.append(f"{skip_lbl}:")

        elif node_type == 'do_step':
            # Nó: ('do_step', label, var, inicio, fim, passo)
            lbl_num, var_name = node[1], node[2]
            start_expr, end_expr, step_expr = node[3], node[4], node[5]

            start_lbl = self.new_label()
            end_lbl = self.new_label()

            # O passo pode ser uma expressão, mas para o contexto do DO guardamos o nó para emitir código na altura do incremento
            self.do_contexts[lbl_num] = {
                'var': var_name,
                'start_lbl': start_lbl,
                'end_lbl': end_lbl,
                'step_expr': step_expr,
                'step': None,
                'current_scope': current_scope
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

        elif node_type == 'continue':
            pass