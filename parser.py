import ply.yacc as yacc
from lexer import tokens

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('left', 'EQ', 'NE', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)

def p_compilation_unit(p):
    '''compilation_unit : unit_list'''
    p[0] = ('compilation_unit', p[1])

def p_unit_list_multiple(p):
    '''unit_list : unit_list unit'''
    p[0] = p[1] + [p[2]]

def p_unit_list_single(p):
    '''unit_list : unit'''
    p[0] = [p[1]]

def p_unit(p):
    '''unit : program
            | function
            | subroutine'''
    p[0] = p[1]

def p_subroutine(p):
    '''subroutine : SUBROUTINE ID LPAREN param_list RPAREN statements END'''
    p[0] = ('subroutine', p[2], p[4], p[6])

def p_program(p):
    '''program : PROGRAM ID statements END'''
    p[0] = ('program', p[2], p[3])

# ================= STATEMENTS =================
def p_statement_call(p):
    '''statement : CALL ID LPAREN arg_list RPAREN'''
    p[0] = ('call_stmt', p[2], p[4])

# Regra para Atribuição de Variáveis (ex: FAT = FAT * I)
def p_statement_assign(p):
    '''statement : ID EQUALS expression'''
    p[0] = ('assign', p[1], p[3])

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
    '''statement : PRINT TIMES COMMA print_list
                 | PRINT COMMA print_list'''
    if len(p) == 5:
        p[0] = ('print', p[4])
    else:
        p[0] = ('print', p[3])

def p_print_list_multiple(p):
    '''print_list : print_list COMMA print_item'''
    p[0] = p[1] + [p[3]]

def p_print_list_single(p):
    '''print_list : print_item'''
    p[0] = [p[1]]

def p_print_item(p):
    '''print_item : STRING
                  | expression'''
    p[0] = p[1]

# ================= SUBPROGRAMAS =================
def p_function(p):
    '''function : type FUNCTION ID LPAREN param_list RPAREN statements END'''
    # Nó: ('function', tipo_retorno, nome_funcao, lista_parametros, comandos)
    p[0] = ('function', p[1], p[3], p[5], p[7])

def p_param_list_multiple(p):
    '''param_list : param_list COMMA ID'''
    p[0] = p[1] + [p[3]]

def p_param_list_single(p):
    '''param_list : ID'''
    p[0] = [p[1]]

def p_param_list_empty(p):
    '''param_list : '''
    p[0] = []

# O comando RETURN é exclusivo dentro de funções/subrotinas
def p_statement_return(p):
    '''statement : RETURN'''
    p[0] = ('return',)

# ================= TYPE E LIST =================
def p_type(p):
    '''type : INTEGER
            | REAL
            | LOGICAL'''
    p[0] = p[1]

def p_id_item_simple(p):
    '''id_item : ID'''
    p[0] = ('id', p[1])

def p_id_item_array(p):
    '''id_item : ID LPAREN NUMBER RPAREN'''
    # Nó: ('array', nome, tamanho)
    p[0] = ('array', p[1], p[3])

def p_id_list(p):
    '''id_list : id_item
               | id_list COMMA id_item'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# Regra para Declaração de Variáveis (ex: INTEGER N, I, FAT)
def p_statement_decl(p):
    '''statement : type id_list'''
    p[0] = ('declare', p[1], p[2])

# ================= ATRIBUIÇÃO E LEITURA DE ARRAYS =================

def p_statement_assign_array(p):
    '''statement : ID LPAREN expression RPAREN EQUALS expression'''
    # Nó: ('assign_array', NOME, INDICE, VALOR)
    p[0] = ('assign_array', p[1], p[3], p[6])

def p_statement_read_array(p):
    '''statement : READ TIMES COMMA ID LPAREN expression RPAREN
                 | READ COMMA ID LPAREN expression RPAREN'''
    # Nó para ler diretamente para dentro do Array (ex: READ *, NUMS(I))
    if len(p) == 8:
        p[0] = ('read_array', p[4], p[6])
    else:
        p[0] = ('read_array', p[3], p[5])

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

def p_expression_func_call(p):
    '''expression : ID LPAREN arg_list RPAREN'''
    p[0] = ('func_call', p[1], p[3])

# O Fortran 77 tem funções matemáticas embutidas MOD(A, B) para calcular o resto da divisão.
def p_expression_mod_call(p):
    '''expression : MOD LPAREN expression COMMA expression RPAREN'''
    p[0] = ('mod_call', p[3], p[5])

def p_arg_list_multiple(p):
    '''arg_list : arg_list COMMA expression'''
    p[0] = p[1] + [p[3]]

def p_arg_list_single(p):
    '''arg_list : expression'''
    p[0] = [p[1]]

def p_arg_list_empty(p):
    '''arg_list : '''
    p[0] = []

# Se a estrutura estiver errada, o PLY chama esta função.
def p_error(p):
    if p:
        print(f"Erro Sintático: Estrutura inválida perto de '{p.value}' na linha {p.lineno}")
    else:
        print("Erro Sintático: Fim de ficheiro inesperado. Falta um 'END'?")

parser = yacc.yacc()