# otimizador.py — Otimizações na AST antes da geração de código
# Inspirado na estrutura de voidbert/PL2025 (optimizer.py):
#   - separação em métodos privados por tipo de otimização
#   - ponto de entrada único optimize()



# Pequeno Resumo das otimizações implementadas:
#   1. Constant Folding — calcula expressões constantes em compile-time
#   2. Álgebra simples — X+0→X, X*1→X, X*0→0, etc.
#   3. IF estático — IF(.TRUE./.FALSE.) resolvidos em compile-time
#   4. UMINUS em constantes — -5 → ('number', -5) directamente
#   5. Double negation — NOT(NOT x) → x
#   6. Negação de comparações — NOT(x .EQ. y) → x .NE. y  (elimina NOT)
#   7. De Morgan — NOT(x .AND. y) → NOT(x) .OR. NOT(y)


class Otimizador:

    # Tabela de operadores opostos (para eliminar NOT em comparações)
    _OPOSTO = {
        '.EQ.': '.NE.', '.NE.': '.EQ.',
        '.LT.': '.GE.', '.GE.': '.LT.',
        '.GT.': '.LE.', '.LE.': '.GT.',
    }

    # Ponto de entrada público

    def optimize(self, node):
        """
        Percorre a AST e aplica todas as otimizações.
        Retorna a AST transformada (imutável — não altera o original).
        """
        if node is None:
            return None
        if isinstance(node, list):
            return self._optimize_list(node)
        if not isinstance(node, tuple):
            return node

        kind = node[0]
        optimizer = getattr(self, f'_opt_{kind}', self._opt_default)
        return optimizer(node)

    # Optimizadores por tipo de nó

    def _optimize_list(self, lst: list) -> list:
        """Otimiza uma lista de statements, removendo nós None."""
        result = []
        for item in lst:
            opt = self.optimize(item)
            if opt is not None:
                result.append(opt)
        return result

    def _opt_default(self, node: tuple) -> tuple:
        """Fallback: percorre os filhos recursivamente."""
        return tuple(
            self.optimize(e) if isinstance(e, (tuple, list)) else e
            for e in node
        )

    # Expressões Binárias

    def _opt_binop(self, node: tuple):
        _, op, left, right = node
        left  = self.optimize(left)
        right = self.optimize(right)

        # 1. Constant Folding
        folded = self._fold_constants(op, left, right)
        if folded is not None:
            return folded

        # 2. Álgebra simples
        simplified = self._simplify_algebra(op, left, right)
        if simplified is not None:
            return simplified

        return ('binop', op, left, right)

    def _fold_constants(self, op, left, right):
        """Calcula operações entre dois literais em tempo de compilação."""
        if left[0] != 'number' or right[0] != 'number':
            return None
        vl, vr = left[1], right[1]
        arith = {'+': vl+vr, '-': vl-vr, '*': vl*vr}
        if op in arith:
            return ('number', arith[op])
        if op == '/' and vr != 0:
            return ('number', int(vl / vr))
        compare = {
            '.EQ.': vl == vr, '.NE.': vl != vr,
            '.LT.': vl <  vr, '.LE.': vl <= vr,
            '.GT.': vl >  vr, '.GE.': vl >= vr,
        }
        if op in compare:
            return ('bool', '.TRUE.' if compare[op] else '.FALSE.')
        return None

    def _simplify_algebra(self, op, left, right):
        """Regras algébricas simples para eliminar operações triviais."""
        zero = ('number', 0)
        one  = ('number', 1)
        if op == '+':
            if right == zero: return left
            if left  == zero: return right
        elif op == '-':
            if right == zero: return left
        elif op == '*':
            if right == one:  return left
            if left  == one:  return right
            if right == zero: return zero
            if left  == zero: return zero
        elif op == '/':
            if right == one:  return left
        return None

    # Minus Unário

    def _opt_uminus(self, node: tuple):
        inner = self.optimize(node[1])
        if inner[0] == 'uminus':          # --x → x
            return inner[1]
        if inner[0] == 'number':           # -5 → number(-5)
            return ('number', -inner[1])
        if inner[0] == 'real':
            return ('real', -inner[1])
        return ('uminus', inner)

    # NOT e leis de De Morgan

    def _opt_not(self, node: tuple):
        inner = self.optimize(node[1])

        # 5. NOT(NOT x) → x
        if inner[0] == 'not':
            return inner[1]

        # 6. NOT(x .EQ. y) → x .NE. y elimina instrução NOT da VM
        if inner[0] == 'binop' and inner[1] in self._OPOSTO:
            return ('binop', self._OPOSTO[inner[1]], inner[2], inner[3])

        # 7. De Morgan
        if inner[0] == 'binop' and inner[1] == '.AND.':
            return self.optimize(
                ('binop', '.OR.', ('not', inner[2]), ('not', inner[3])))
        if inner[0] == 'binop' and inner[1] == '.OR.':
            return self.optimize(
                ('binop', '.AND.', ('not', inner[2]), ('not', inner[3])))

        return ('not', inner)

    # ── IF estático ───────────────────────────────────────────────────────────

    def _opt_if(self, node: tuple):
        _, cond, body = node
        cond = self.optimize(cond)
        if cond == ('bool', '.TRUE.'):
            return self.optimize(body)    # mantém só o corpo
        if cond == ('bool', '.FALSE.'):
            return None                   # bloco desaparece
        return ('if', cond, self.optimize(body))

    def _opt_if_else(self, node: tuple):
        _, cond, then_body, else_body = node
        cond = self.optimize(cond)
        if cond == ('bool', '.TRUE.'):
            return self.optimize(then_body)
        if cond == ('bool', '.FALSE.'):
            return self.optimize(else_body)
        return ('if_else', cond,
                self.optimize(then_body),
                self.optimize(else_body))