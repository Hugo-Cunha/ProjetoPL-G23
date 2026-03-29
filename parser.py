import ply.yacc as yacc

# Precisamos de importar a lista de tokens do nosso lexer
from lexer import tokens

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('left', 'EQ', 'NE', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)

def p_program(p):
    '''program : PROGRAM ID statements END'''
    # p[1] = PROGRAM
    # p[2] = ID (ex: HELLO)
    # p[3] = statements (a lista de comandos que processámos abaixo)
    # p[4] = END
    # Vamos devolver um tuplo que representa o nó principal da nossa árvore
    p[0] = ('program', p[2], p[3])

# ================= STATEMENTS =================
# Regra para Atribuição de Variáveis (ex: FAT = FAT * I)
def p_statement_assign(p):
    '''statement : ID EQUALS expression'''
    p[0] = ('assign', p[1], p[3])

# Regra para Declaração de Variáveis (ex: INTEGER N, I, FAT)
def p_statement_decl(p):
    '''statement : type id_list'''
    p[0] = ('declare', p[1], p[2])

def p_statement_if(p):
    '''statement : IF LPAREN expression RPAREN THEN statements ENDIF'''
    # Nó: ('if', condicao, bloco_verdadeiro)
    p[0] = ('if', p[3], p[6])

def p_statement_if_else(p):
    '''statement : IF LPAREN expression RPAREN THEN statements ELSE statements ENDIF'''
    # Nó: ('if_else', condicao, bloco_verdadeiro, bloco_falso)
    p[0] = ('if_else', p[3], p[6], p[8])


def p_statements_multiple(p):
    '''statements : statements statement'''
    p[0] = p[1] + [p[2]]  # Junta o novo comando à lista existente


def p_statements_single(p):
    '''statements : statement'''
    p[0] = [p[1]]  # Cria uma lista com o primeiro comando

def p_statement_read(p):
    '''statement : READ TIMES COMMA ID
                 | READ COMMA ID'''
    # O READ guarda o valor numa variável (ID)
    if len(p) == 5:
        p[0] = ('read', p[4])
    else:
        p[0] = ('read', p[3])

def p_statement_goto(p):
    '''statement : GOTO NUMBER'''
    p[0] = ('goto', p[2])

def p_statement_continue(p):
    '''statement : CONTINUE'''
    p[0] = ('continue',)

def p_statement_do(p):
    '''statement : DO NUMBER ID EQUALS expression COMMA expression'''
    # Estrutura: DO label variavel = inicio, fim (ex: DO 10 I = 1, N)
    p[0] = ('do', p[2], p[3], p[5], p[7])

def p_statement_labeled(p):
    '''statement : NUMBER statement'''
    p[0] = ('label', p[1], p[2])

def p_statement_print(p):
    '''statement : PRINT TIMES COMMA STRING
                 | PRINT COMMA STRING
                 | PRINT TIMES COMMA expression
                 | PRINT COMMA expression'''
    # Se o tamanho for 5, apanhou a versão com o asterisco (PRINT *, ...)
    if len(p) == 5:
        p[0] = ('print', p[4])
    else:
        p[0] = ('print', p[3])

# ================= TYPE E LIST =================
def p_type(p):
    '''type : INTEGER
            | REAL
            | LOGICAL'''
    p[0] = p[1]

# Como uma declaração pode ter várias variáveis separadas por vírgula,
# criamos uma regra recursiva elegante para capturar a lista toda.
def p_id_list(p):
    '''id_list : ID
               | id_list COMMA ID'''
    if len(p) == 2:
        p[0] = [p[1]]             # Se for só um ID, cria uma lista com ele
    else:
        p[0] = p[1] + [p[3]]      # Se tiver vírgula, junta o novo ID à lista existente


# ================= EXPRESSIONS =================
# O parser já sabe a precedência matemática graças à variável `precedence` lá em cima!
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression'''
    p[0] = ('binop', p[2], p[1], p[3]) # Guardamos: (operador, lado_esquerdo, lado_direito)

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2] # Ignoramos os parênteses na AST, só servem para forçar precedência no parsing

def p_expression_number(p):
    '''expression : NUMBER'''
    p[0] = ('number', p[1])

def p_expression_id(p):
    '''expression : ID'''
    p[0] = ('id', p[1])

def p_expression_relational_logical(p):
    '''expression : expression AND expression
                | expression OR expression
                | expression EQ expression
                | expression NE expression
                | expression LT expression
                | expression LE expression
                | expression GT expression
                | expression GE expression'''
    p[0] = ('binop', p[2], p[1], p[3])

def p_expression_not(p):
    '''expression : NOT expression'''
    p[0] = ('not', p[2])

def p_expression_bool(p):
    '''expression : TRUE
                  | FALSE'''
    p[0] = ('bool', p[1])

# Se a estrutura estiver errada, o PLY chama esta função.
def p_error(p):
    if p:
        print(f"Erro Sintático: Estrutura inválida perto de '{p.value}' na linha {p.lineno}")
    else:
        print("Erro Sintático: Fim de ficheiro inesperado. Falta um 'END'?")

parser = yacc.yacc()

if __name__ == '__main__':
    codigo_teste = '''
    PROGRAM FATORIAL
    INTEGER N, I, FAT
    READ *, N
    FAT = 1
    DO 10 I = 1, N
    FAT = FAT * I
    10 CONTINUE
    PRINT *, FAT
    END
    '''

    print("A iniciar o Teste Final do Parser (Fatorial)...")
    print("-" * 50)
    resultado_ast = parser.parse(codigo_teste)

    import pprint

    print("Árvore de Sintaxe Abstrata (AST) gerada:")
    pprint.pprint(resultado_ast)
    print("-" * 50)