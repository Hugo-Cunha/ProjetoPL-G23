# lexer.py
# Analisador Léxico para Fortran 77 (formato livre)
# Inspirado na estrutura de classe do projeto voidbert/PL2025,

import re

import ply.lex as lex

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
             'ID',
             'NUMBER',
             'REAL_NUMBER',
             'PLUS',  # +
             'MINUS',  # -
             'TIMES',  # *
             'DIVIDE',  # /
             'EQUALS',  # =
             'LPAREN',  # (
             'RPAREN',  # )
             'COMMA',  # ,
             'STRING',  # 'texto entre aspas simples'

             # Operadores lógicos/relacionais
             'TRUE',  # .TRUE.
             'FALSE',  # .FALSE.
             'AND',  # .AND.
             'OR',  # .OR.
             'NOT',  # .NOT.
             'EQ',  # .EQ.   (==)
             'NE',  # .NE.   (!=)
             'LT',  # .LT.   (<)
             'LE',  # .LE.   (<=)
             'GT',  # .GT.   (>)
             'GE',  # .GE.   (>=)
         ] + list(reserved.values())
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_EQUALS = r'='
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','


# Operadores do Fortran (têm pontos à volta)
def t_TRUE(t):
    r'\.TRUE\.'
    return t


def t_FALSE(t):
    r'\.FALSE\.'
    return t


def t_AND(t):
    r'\.AND\.'
    return t


def t_OR(t):
    r'\.OR\.'
    return t


def t_NOT(t):
    r'\.NOT\.'
    return t


def t_EQ(t):
    r'\.EQ\.'
    return t


def t_NE(t):
    r'\.NE\.'
    return t


def t_LT(t):
    r'\.LT\.'
    return t


def t_LE(t):
    r'\.LE\.'
    return t


def t_GT(t):
    r'\.GT\.'
    return t


def t_GE(t):
    r'\.GE\.'
    return t


# Strings Fortran: entre aspas simples, '' dentro da string representa uma aspa literal
def t_STRING(t):
    r"'([^']|'')*'"
    # Remove as aspas externas e converte '' → '
    t.value = t.value[1:-1].replace("''", "'")
    return t


# REGRAS PARA NÚMEROS

def t_REAL_NUMBER(t):
    r'\d+\.\d+'
    # Definida ANTES de t_NUMBER para que o PLY case o real primeiro
    t.value = float(t.value)
    return t


def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    # Fortran é case-insensitive: normalizamos sempre para maiúsculas
    upper = t.value.upper()
    t.type = reserved.get(upper, 'ID')
    t.value = upper
    return t


# Regra para contar o número de linhas (útil para mensagens de erro)
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_COMMENT_INLINE(t):
    r'!.*'
    pass


# Ignorar espaços em branco e tabulações (A grande vantagem do formato livre!)
t_ignore = ' \t'

_last_error = None


def t_error(t):
    global _last_error
    pos = t.lexer.lexpos
    if _last_error is not None:
        start, length = _last_error
        if start + length == pos:
            _last_error = (start, length + 1)
        else:
            _flush_error(t.lexer)
            _last_error = (pos, 1)
    else:
        _last_error = (pos, 1)
    t.lexer.skip(1)


def _flush_error(lexer):
    global _last_error
    if _last_error is not None:
        start, length = _last_error
        bad = lexer.lexdata[start:start + length]
        print(f"Erro Léxico (linha {lexer.lineno}): caractere(s) não reconhecido(s): {repr(bad)}")
        _last_error = None


def t_eof(t):
    _flush_error(t.lexer)

def preprocessar(codigo):
    """
    Remove linhas de comentário Fortran 77 (C ou c na coluna 1).
    Deve ser chamada antes de parser.parse(codigo).
    """
    linhas = codigo.splitlines(keepends=True)
    resultado = []
    for linha in linhas:
        # Linha de comentário: começa com C/c (ignorando \r no Windows)
        stripped = linha.lstrip('\r')
        if stripped and stripped[0] in ('C', 'c'):
            # Substitui por linha vazia para preservar numeração
            resultado.append('\n')
        else:
            resultado.append(linha)
    return ''.join(resultado)

# Cria o analisador léxico
lexer = lex.lex()
