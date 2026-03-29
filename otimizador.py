class Otimizador:
    def optimize(self, node):
        if node is None:
            return None

        # Se for uma lista (ex: bloco de comandos), otimiza cada um
        if isinstance(node, list):
            return [self.optimize(n) for n in node]

        # Se não for um tuplo devolve como está
        if not isinstance(node, tuple):
            return node

        node_type = node[0]

        # O nosso alvo principal: Operações Binárias (Contas)
        if node_type == 'binop':
            # node = ('binop', operador, lado_esquerdo, lado_direito)
            op = node[1]

            # 1. Primeiro tentamos otimizar os filhos
            left = self.optimize(node[2])
            right = self.optimize(node[3])
            # 2. CONSTANT FOLDING: Se ambos os lados ficaram reduzidos a números puros!
            if left[0] == 'number' and right[0] == 'number':
                val_left = left[1]
                val_right = right[1]
                # Fazemos a matemática na hora da compilação!
                if op == '+':
                    return ('number', val_left + val_right)
                elif op == '-':
                    return ('number', val_left - val_right)
                elif op == '*':
                    return ('number', val_left * val_right)
                elif op == '/':
                    if val_right != 0:  # Segurança para não dar erro no Python
                        return ('number', int(val_left / val_right))
            # Se não deu para otimizar (ex: X + 5), devolvemos o nó com os filhos (que podem estar otimizados)
            return ('binop', op, left, right)

        elif node_type == 'if':
            # node = ('if', condicao, bloco)
            cond = self.optimize(node[1])
            if cond == ('bool', '.TRUE.'):
                return self.optimize(node[2])  # Fica só o código de dentro
            if cond == ('bool', '.FALSE.'):
                return None
            return ('if', cond, self.optimize(node[2]))

        elif node_type == 'if_else':
            cond = self.optimize(node[1])
            if cond == ('bool', '.TRUE.'): return self.optimize(node[2])
            if cond == ('bool', '.FALSE.'): return self.optimize(node[3])
            return ('if_else', cond, self.optimize(node[2]), self.optimize(node[3]))

        optimized_node = []
        for element in node:
            optimized_node.append(self.optimize(element))

        return tuple(optimized_node)