# lexer.py
# Inpirado por Humberto Gomes (2023)
# Analisador Léxico para Fortran 77 (formato livre) orientado a objetos

import ply.lex as lex


class Lexer:
    # As palavras reservadas e os tokens têm de estar ao nível da classe
    reserved = {
        'PROGRAM': 'PROGRAM',
        'INTEGER': 'INTEGER',
        'REAL': 'REAL',
        'LOGICAL': 'LOGICAL',
        'IF': 'IF',
        'THEN': 'THEN',
        'ELSE': 'ELSE',
        'ENDIF': 'ENDIF',
        'DO': 'DO',
        'GOTO': 'GOTO',
        'CONTINUE': 'CONTINUE',
        'PRINT': 'PRINT',
        'READ': 'READ',
        'END': 'END',
        'FUNCTION': 'FUNCTION',
        'RETURN': 'RETURN',
        'MOD': 'MOD',
        'SUBROUTINE': 'SUBROUTINE',
        'CALL': 'CALL',
    }

    tokens = [
                 'ID', 'NUMBER', 'REAL_NUMBER', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
                 'EQUALS', 'LPAREN', 'RPAREN', 'COMMA', 'STRING',
                 'TRUE', 'FALSE', 'AND', 'OR', 'NOT', 'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
             ] + list(reserved.values())

    # As expressões regulares simples também ficam ao nível da classe
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_EQUALS = r'='
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_COMMA = r','

    # Ignorar espaços e tabs
    t_ignore = ' \t'

    def __init__(self):
        # Variável de estado para gestão de erros
        self._last_error = None
        # O módulo 'self' diz ao PLY para procurar as regras dentro desta instância!
        self.lexer = lex.lex(module=self)

    # Todos os métodos ganham o parâmetro 'self'
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

    def t_STRING(self, t):
        r"'([^']|'')*'"
        t.value = t.value[1:-1].replace("''", "'")
        return t

    def t_REAL_NUMBER(self, t):
        r'\d+\.\d+'
        t.value = float(t.value)
        return t

    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        upper = t.value.upper()
        # Acedemos ao dicionário reserved usando o 'self'
        t.type = self.reserved.get(upper, 'ID')
        t.value = upper
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_COMMENT_INLINE(self, t):
        r'!.*'
        pass

    # GESTÃO DE ERROS LÉXICOS (sem usar global)
    def t_error(self, t):
        pos = t.lexer.lexpos
        if self._last_error is not None:
            start, length = self._last_error
            if start + length == pos:
                self._last_error = (start, length + 1)
            else:
                self._flush_error(t.lexer)
                self._last_error = (pos, 1)
        else:
            self._last_error = (pos, 1)
        t.lexer.skip(1)

    def _flush_error(self, lexer):
        if self._last_error is not None:
            start, length = self._last_error
            bad = lexer.lexdata[start:start + length]
            print(f"Erro Léxico (linha {lexer.lineno}): caractere(s) não reconhecido(s): {repr(bad)}")
            self._last_error = None

    def t_eof(self, t):
        self._flush_error(t.lexer)

    # UTILITÁRIOS
    def preprocessar(self, codigo):
        """Remove linhas de comentário Fortran 77"""
        linhas = codigo.splitlines(keepends=True)
        resultado = []
        for linha in linhas:
            stripped = linha.lstrip('\r')
            if stripped and stripped[0] in ('C', 'c'):
                resultado.append('\n')
            else:
                resultado.append(linha)
        return ''.join(resultado)
