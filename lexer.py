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
    'FUNCTION': 'FUNCTION', # Para a etapa de valorização
    'RETURN': 'RETURN',     # Para a etapa de valorização
    'MOD': 'MOD'            # Função embutida usada nos exemplos
}

tokens = [
    'ID',       # Nomes de variáveis (ex: SOMA, NUMS)
    'NUMBER',   # Números inteiros (nesta fase)
    'PLUS',     # +
    'MINUS',    # -
    'TIMES',    # *
    'DIVIDE',   # /
    'EQUALS',   # =
    'LPAREN',   # (
    'RPAREN',   # )
    'COMMA',    # ,
    'STRING',   # Textos entre aspas simples (ex: 'ola, Mundo!')
    # Operadores lógicos e relacionais específicos do Fortran (.TRUE., .EQ., etc.)
    'TRUE',
    'FALSE',
    'AND',
    'OR',
    'NOT',
    'EQ',
    'NE',
    'LT',
    'LE',
    'GT',
    'GE'
] + list(reserved.values())

t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_EQUALS  = r'='
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_COMMA   = r','

# Operadores do Fortran (têm pontos à volta)
t_TRUE  = r'\.TRUE\.'
t_FALSE = r'\.FALSE\.'
t_AND   = r'\.AND\.'
t_OR    = r'\.OR\.'
t_NOT   = r'\.NOT\.'
t_EQ    = r'\.EQ\.'
t_NE    = r'\.NE\.'
t_LT    = r'\.LT\.'
t_LE    = r'\.LE\.'
t_GT    = r'\.GT\.'
t_GE    = r'\.GE\.'

# Strings (tudo o que estiver entre aspas simples)
t_STRING = r"'.*?'"

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    # Converte o valor para maiúsculas para verificar no dicionário 'reserved'
    # Se não encontrar, o tipo por defeito é 'ID' (variável normal)
    t.type = reserved.get(t.value.upper(), 'ID')
    return t

# Números: Sequência de dígitos
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value) # Converte a string capturada para um inteiro real no Python
    return t

# Regra para contar o número de linhas (útil para mensagens de erro)
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Ignorar espaços em branco e tabulações (A grande vantagem do formato livre!)
t_ignore  = ' \t'

# Função de tratamento de erros léxicos
def t_error(t):
    print(f"Erro Léxico: Caractere ilegal '{t.value[0]}' na linha {t.lineno}")
    t.lexer.skip(1) # Ignora o caractere problemático e continua

# Cria o analisador léxico
lexer = lex.lex()

if __name__ == '__main__':
    # Este é o Exemplo 1 do guião, guardado numa string para teste rápido
    codigo_teste = '''
    PROGRAM HELLO
    PRINT *, 'ola, Mundo!'
    END
    '''

    # Alimentar o nosso lexer com o código de teste
    lexer.input(codigo_teste)

    # Ciclo para pedir ao lexer os tokens um a um até acabar
    print("A iniciar a Análise Léxica...")
    print("-" * 30)

    for token in lexer:
        # Imprime o tipo do token, o valor capturado, a linha e a posição
        print(f"Tipo: {token.type:8} | Valor: {token.value}")

    print("-" * 30)
    print("Análise Léxica concluída!")