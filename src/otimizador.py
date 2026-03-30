class Otimizador:
    _OPOSTO = {
        '.EQ.': '.NE.', '.NE.': '.EQ.',
        '.LT.': '.GE.', '.GE.': '.LT.',
        '.GT.': '.LE.', '.LE.': '.GT.',
    }

    def optimize(self, node):
        if node is None:
            return None

        if isinstance(node, list):
            resultado = []
            for n in node:
                opt = self.optimize(n)
                if opt is not None:
                    resultado.append(opt)
            return resultado

        if not isinstance(node, tuple):
            return node

        node_type = node[0]

        if node_type == 'binop':
            # node = ('binop', op, left, right)
            op = node[1]
            left = self.optimize(node[2])
            right = self.optimize(node[3])

            # Constant Folding: ambos os lados são números → calcula já em compile-time
            if left[0] == 'number' and right[0] == 'number':
                vl, vr = left[1], right[1]
                if op == '+': return ('number', vl + vr)
                if op == '-': return ('number', vl - vr)
                if op == '*': return ('number', vl * vr)
                if op == '/' and vr != 0: return ('number', int(vl / vr))
                if op == '.EQ.': return ('bool', '.TRUE.' if vl == vr else '.FALSE.')
                if op == '.NE.': return ('bool', '.TRUE.' if vl != vr else '.FALSE.')
                if op == '.LT.': return ('bool', '.TRUE.' if vl < vr else '.FALSE.')
                if op == '.LE.': return ('bool', '.TRUE.' if vl <= vr else '.FALSE.')
                if op == '.GT.': return ('bool', '.TRUE.' if vl > vr else '.FALSE.')
                if op == '.GE.': return ('bool', '.TRUE.' if vl >= vr else '.FALSE.')

            # Álgebra simples:  X + 0, X * 1, X * 0, 0 + X, 1 * X
            if op == '+':
                if right == ('number', 0): return left
                if left  == ('number', 0): return right
            elif op == '-':
                if right == ('number', 0): return left
            elif op == '*':
                if right == ('number', 1): return left
                if left  == ('number', 1): return right
                if right == ('number', 0): return ('number', 0)
                if left  == ('number', 0): return ('number', 0)
            elif op == '/':
                if right == ('number', 1): return left

            return ('binop', op, left, right)

        elif node_type == 'uminus':
            # node = ('uminus', inner)
            inner = self.optimize(node[1])
            # Dobrar o sinal: --X → X
            if inner[0] == 'uminus':
                return inner[1]
            # Constante negativa
            if inner[0] == 'number':
                return ('number', -inner[1])
            return ('uminus', inner)

        elif node_type == 'not':
            # node = ('not', inner)
            inner = self.optimize(node[1])
            # NOT(NOT x) → x
            if inner[0] == 'not':
                return inner[1]
            # NOT(x .OP. y) → x .OPOSTO. y   (elimina instrução NOT)
            if inner[0] == 'binop' and inner[1] in self._OPOSTO:
                return ('binop', self._OPOSTO[inner[1]], inner[2], inner[3])
            # De Morgan — NOT(x .AND. y) → NOT(x) .OR. NOT(y)
            #              — NOT(x .OR. y)  → NOT(x) .AND. NOT(y)
            if inner[0] == 'binop' and inner[1] == '.AND.':
                return self.optimize(('binop', '.OR.',
                                      ('not', inner[2]), ('not', inner[3])))
            if inner[0] == 'binop' and inner[1] == '.OR.':
                return self.optimize(('binop', '.AND.',
                                      ('not', inner[2]), ('not', inner[3])))

            return ('not', inner)

        elif node_type == 'if':
            # node = ('if', cond, then)
            cond = self.optimize(node[1])
            if cond == ('bool', '.TRUE.'):
                return self.optimize(node[2])
            if cond == ('bool', '.FALSE.'):
                return None
            return ('if', cond, self.optimize(node[2]))

        elif node_type == 'if_else':
            # node = ('if_else', cond, then, else)
            cond = self.optimize(node[1])
            if cond == ('bool', '.TRUE.'): return self.optimize(node[2])
            if cond == ('bool', '.FALSE.'): return self.optimize(node[3])
            return ('if_else', cond, self.optimize(node[2]), self.optimize(node[3]))

        # Para todos os outros nós, otimiza recursivamente os filhos
        return tuple(self.optimize(e) if isinstance(e, (tuple, list)) else e for e in node)