# lexer.py — Analisador Léxico para Fortran 77
# Estrutura de classe inspirada em voidbert/PL2025:
#   - tokens e reserved ao nível da classe (necessário para o PLY)
#   - regras como métodos de instância
#   - gestão de erros acumulada (agrupa erros consecutivos)
#   - pré-processamento de comentários C-coluna-1 encapsulado na classe

import ply.lex as lex


class Lexer:

    # Palavras reservadas — ao nível da classe para o PLY e o Parser acederem
    reserved = {
        'PROGRAM':    'PROGRAM',
        'INTEGER':    'INTEGER',
        'REAL':       'REAL',
        'LOGICAL':    'LOGICAL',
        'IF':         'IF',
        'THEN':       'THEN',
        'ELSE':       'ELSE',
        'ENDIF':      'ENDIF',
        'DO':         'DO',
        'GOTO':       'GOTO',
        'CONTINUE':   'CONTINUE',
        'PRINT':      'PRINT',
        'READ':       'READ',
        'END':        'END',
        'FUNCTION':   'FUNCTION',
        'RETURN':     'RETURN',
        'MOD':        'MOD',
        'SQRT':         'SQRT',
        'ABS':          'ABS',
        'SUBROUTINE': 'SUBROUTINE',
        'CALL':       'CALL',
    }

    # Lista de tokens — ao nível da classe (o PLY exige isso)
    tokens = [
        'ID', 'NUMBER', 'REAL_NUMBER',
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'POWER', 'EQUALS',
        'LPAREN', 'RPAREN', 'COMMA', 'STRING',
        'TRUE', 'FALSE',
        'AND', 'OR', 'NOT',
        'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
    ] + list(reserved.values())

    # Regras simples (strings) — ao nível da classe o PLY ordena-as por comprimento decrescente automaticamente
    t_PLUS   = r'\+'
    t_MINUS  = r'-'
    t_TIMES  = r'\*'
    t_DIVIDE = r'/'
    t_EQUALS = r'='
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_COMMA  = r','
    t_ignore = ' \t\r'

    def __init__(self):
        self._last_error = None          # estado para agrupamento de erros
        self.lexer = lex.lex(module=self)

    # Operadores lógicos/relacionais do Fortran (pontos à volta)
    # Definidos como funções para ter prioridade sobre t_ID
    def t_TRUE(self, t):
        r'\.TRUE\.'
        return t

    def t_FALSE(self, t):
        r'\.FALSE\.'
        return t

    def t_AND(self, t):
        r'\.AND\.'
        return t

    def t_OR(self, t):
        r'\.OR\.'
        return t

    def t_NOT(self, t):
        r'\.NOT\.'
        return t

    def t_EQ(self, t):
        r'\.EQ\.'
        return t

    def t_NE(self, t):
        r'\.NE\.'
        return t

    def t_LT(self, t):
        r'\.LT\.'
        return t

    def t_LE(self, t):
        r'\.LE\.'
        return t

    def t_GT(self, t):
        r'\.GT\.'
        return t

    def t_GE(self, t):
        r'\.GE\.'
        return t

    # Strings Fortran: entre aspas simples, '' dentro representa uma aspa
    def t_STRING(self, t):
        r"'([^']|'')*'"
        t.value = t.value[1:-1].replace("''", "'")
        return t

    def t_POWER(self, t):
        r'\*\*'
        return t

    # Números — REAL_NUMBER antes de NUMBER para que o PLY tente o real primeiro
    def t_REAL_NUMBER(self, t):
        r'\d+\.\d+'
        t.value = float(t.value)
        return t

    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    # Identificadores e palavras reservadas
    # Fortran é case-insensitive: normaliza sempre para maiúsculas
    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        upper   = t.value.upper()
        t.type  = self.reserved.get(upper, 'ID')
        t.value = upper
        return t

    # Comentários inline (! em qualquer coluna)
    # Comentários C-coluna-1 são tratados em preprocessar() antes do lexer
    def t_COMMENT_INLINE(self, t):
        r'!.*'
        pass   # descarta silenciosamente

    # Newlines — actualiza o contador de linhas
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # Gestão de erros léxicos
    # Agrupa caracteres inválidos consecutivos numa só mensagem
    def t_error(self, t):
        pos = t.lexer.lexpos
        if self._last_error is not None:
            start, length = self._last_error
            if start + length == pos:
                self._last_error = (start, length + 1)   # continua o bloco
            else:
                self._flush_error(t.lexer)
                self._last_error = (pos, 1)
        else:
            self._last_error = (pos, 1)
        t.lexer.skip(1)

    def t_eof(self, t):
        """Chamado no fim do ficheiro — garante que o último erro é emitido."""
        self._flush_error(t.lexer)

    def _flush_error(self, lexer):
        """Emite a mensagem de erro acumulada e limpa o estado."""
        if self._last_error is not None:
            start, length = self._last_error
            bad = lexer.lexdata[start:start + length]
            print(f"Erro Léxico (linha {lexer.lineno}): "
                  f"caractere(s) não reconhecido(s): {repr(bad)}")
            self._last_error = None

    # Pré-processamento
    # Remove linhas de comentário Fortran 77 (C/c na coluna 1).
    def preprocessar(self, codigo: str) -> str:
        """
        Remove linhas de comentário Fortran 77 (C ou c na coluna 1).
        Substitui por linha vazia para preservar a numeração de linhas
        nas mensagens de erro.
        """
        linhas = codigo.splitlines(keepends=True)
        resultado = []
        for linha in linhas:
            stripped = linha.lstrip('\r')
            if stripped and stripped[0] in ('C', 'c'):
                resultado.append('\n')
            else:
                resultado.append(linha)
        return ''.join(resultado)