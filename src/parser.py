# parser.py — Analisador Sintático para Fortran 77
# Estrutura de classe: tokens e precedência ao nível da classe

import ply.yacc as yacc
from lexer import Lexer


class Parser:

    # tokens e precedence têm de ser atributos de classe (o PLY exige)
    tokens = Lexer.tokens

    precedence = (
        ('left',  'OR'),
        ('left',  'AND'),
        ('right', 'NOT'),
        ('left',  'EQ', 'NE', 'LT', 'LE', 'GT', 'GE'),
        ('left',  'PLUS', 'MINUS'),
        ('left',  'TIMES', 'DIVIDE'),
        ('right', 'UMINUS'),
    )

    def __init__(self):
        self.parser = yacc.yacc(module=self)

    def parse(self, codigo: str, lexer=None):
        """Ponto de entrada público — aceita código fonte e lexer opcional."""
        return self.parser.parse(codigo, lexer=lexer)

    # UNIDADES DE COMPILAÇÃO

    def p_compilation_unit(self, p):
        '''compilation_unit : unit_list'''
        p[0] = ('compilation_unit', p[1])

    def p_unit_list_multiple(self, p):
        '''unit_list : unit_list unit'''
        p[0] = p[1] + [p[2]]

    def p_unit_list_single(self, p):
        '''unit_list : unit'''
        p[0] = [p[1]]

    def p_unit(self, p):
        '''unit : program
                | function
                | subroutine'''
        p[0] = p[1]

    def p_program(self, p):
        '''program : PROGRAM ID statements END'''
        p[0] = ('program', p[2], p[3])

    def p_function(self, p):
        '''function : type FUNCTION ID LPAREN param_list RPAREN statements END'''
        p[0] = ('function', p[1], p[3], p[5], p[7])

    def p_subroutine(self, p):
        '''subroutine : SUBROUTINE ID LPAREN param_list RPAREN statements END'''
        p[0] = ('subroutine', p[2], p[4], p[6])

    # STATEMENTS

    def p_statements_multiple(self, p):
        '''statements : statements statement'''
        p[0] = p[1] + [p[2]]

    def p_statements_single(self, p):
        '''statements : statement'''
        p[0] = [p[1]]

    def p_statement_labeled(self, p):
        '''statement : NUMBER statement'''
        p[0] = ('label', p[1], p[2])

    def p_statement_decl(self, p):
        '''statement : type id_list'''
        p[0] = ('declare', p[1], p[2])

    def p_statement_assign(self, p):
        '''statement : ID EQUALS expression'''
        p[0] = ('assign', p[1], p[3])

    def p_statement_assign_array(self, p):
        '''statement : ID LPAREN expression RPAREN EQUALS expression'''
        p[0] = ('assign_array', p[1], p[3], p[6])

    def p_statement_if(self, p):
        '''statement : IF LPAREN expression RPAREN THEN statements ENDIF'''
        p[0] = ('if', p[3], p[6])

    def p_statement_if_else(self, p):
        '''statement : IF LPAREN expression RPAREN THEN statements ELSE statements ENDIF'''
        p[0] = ('if_else', p[3], p[6], p[8])

    def p_statement_do(self, p):
        '''statement : DO NUMBER ID EQUALS expression COMMA expression'''
        p[0] = ('do', p[2], p[3], p[5], p[7])

    def p_statement_do_step(self, p):
        '''statement : DO NUMBER ID EQUALS expression COMMA expression COMMA expression'''
        p[0] = ('do_step', p[2], p[3], p[5], p[7], p[9])

    def p_statement_goto(self, p):
        '''statement : GOTO NUMBER'''
        p[0] = ('goto', p[2])

    def p_statement_continue(self, p):
        '''statement : CONTINUE'''
        p[0] = ('continue',)

    def p_statement_return(self, p):
        '''statement : RETURN'''
        p[0] = ('return',)

    def p_statement_call(self, p):
        '''statement : CALL ID LPAREN arg_list RPAREN'''
        p[0] = ('call_stmt', p[2], p[4])

    def p_statement_print(self, p):
        '''statement : PRINT TIMES COMMA print_list
                     | PRINT COMMA print_list'''
        p[0] = ('print', p[4] if len(p) == 5 else p[3])

    def p_statement_read(self, p):
        '''statement : READ TIMES COMMA ID
                     | READ COMMA ID'''
        p[0] = ('read', p[4] if len(p) == 5 else p[3])

    def p_statement_read_array(self, p):
        '''statement : READ TIMES COMMA ID LPAREN expression RPAREN
                     | READ COMMA ID LPAREN expression RPAREN'''
        if len(p) == 8:
            p[0] = ('read_array', p[4], p[6])
        else:
            p[0] = ('read_array', p[3], p[5])

    # LISTAS DE PRINT

    def p_print_list_multiple(self, p):
        '''print_list : print_list COMMA print_item'''
        p[0] = p[1] + [p[3]]

    def p_print_list_single(self, p):
        '''print_list : print_item'''
        p[0] = [p[1]]

    def p_print_item_string(self, p):
        '''print_item : STRING'''
        # Envolve em nó ('string', valor) para distinguir de expressões numéricas
        # e permitir ao codegen emitir pushs+writes em vez de writei
        p[0] = ('string', p[1])

    def p_print_item_expr(self, p):
        '''print_item : expression'''
        p[0] = p[1]

    # TIPOS E LISTAS DE DECLARAÇÃO

    def p_type(self, p):
        '''type : INTEGER
                | REAL
                | LOGICAL'''
        p[0] = p[1]

    def p_id_list(self, p):
        '''id_list : id_item
                   | id_list COMMA id_item'''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

    def p_id_item_simple(self, p):
        '''id_item : ID'''
        p[0] = ('id', p[1])

    def p_id_item_array(self, p):
        '''id_item : ID LPAREN NUMBER RPAREN'''
        p[0] = ('array', p[1], p[3])

    # LISTAS DE PARÂMETROS E ARGUMENTOS

    def p_param_list_multiple(self, p):
        '''param_list : param_list COMMA ID'''
        p[0] = p[1] + [p[3]]

    def p_param_list_single(self, p):
        '''param_list : ID'''
        p[0] = [p[1]]

    def p_param_list_empty(self, p):
        '''param_list : '''
        p[0] = []

    def p_arg_list_multiple(self, p):
        '''arg_list : arg_list COMMA expression'''
        p[0] = p[1] + [p[3]]

    def p_arg_list_single(self, p):
        '''arg_list : expression'''
        p[0] = [p[1]]

    def p_arg_list_empty(self, p):
        '''arg_list : '''
        p[0] = []

    # EXPRESSÕES

    def p_expression_binop(self, p):
        '''expression : expression PLUS  expression
                      | expression MINUS expression
                      | expression TIMES expression
                      | expression DIVIDE expression'''
        p[0] = ('binop', p[2], p[1], p[3])

    def p_expression_relational_logical(self, p):
        '''expression : expression AND expression
                      | expression OR  expression
                      | expression EQ  expression
                      | expression NE  expression
                      | expression LT  expression
                      | expression LE  expression
                      | expression GT  expression
                      | expression GE  expression'''
        p[0] = ('binop', p[2], p[1], p[3])

    def p_expression_uminus(self, p):
        '''expression : MINUS expression %prec UMINUS'''
        p[0] = ('uminus', p[2])

    def p_expression_not(self, p):
        '''expression : NOT expression'''
        p[0] = ('not', p[2])

    def p_expression_group(self, p):
        '''expression : LPAREN expression RPAREN'''
        p[0] = p[2]

    def p_expression_number(self, p):
        '''expression : NUMBER'''
        p[0] = ('number', p[1])

    def p_expression_real(self, p):
        '''expression : REAL_NUMBER'''
        p[0] = ('real', p[1])

    def p_expression_bool(self, p):
        '''expression : TRUE
                      | FALSE'''
        p[0] = ('bool', p[1])

    def p_expression_id(self, p):
        '''expression : ID'''
        p[0] = ('id', p[1])

    def p_expression_func_call(self, p):
        '''expression : ID LPAREN arg_list RPAREN'''
        p[0] = ('func_call', p[1], p[3])

    def p_expression_mod_call(self, p):
        '''expression : MOD LPAREN expression COMMA expression RPAREN'''
        p[0] = ('mod_call', p[3], p[5])

    def p_expression_power(self, p):
        '''expression : expression POWER expression'''
        # Operador de exponenciação: base ** expoente
        # Ex: X**2, 2**N, (A+B)**3
        p[0] = ('power', p[1], p[3])

    def p_expression_sqrt(self, p):
        '''expression : SQRT LPAREN expression RPAREN'''
        # Função intrínseca raiz quadrada: SQRT(X)
        # Na EWVM não existe instrução nativa — expandimos para X**(1/2) via itof/sqrt
        # Implementamos como nó ('sqrt', expr) para geração explícita no codegen
        p[0] = ('sqrt', p[3])

    def p_expression_abs(self, p):
        '''expression : ABS LPAREN expression RPAREN'''
        # Função intrínseca valor absoluto: ABS(X)
        p[0] = ('abs', p[3])

    # ERROS

    def p_error(self, p):
        if p:
            print(f"Erro Sintático: token inesperado '{p.value}' na linha {p.lineno}")
        else:
            print("Erro Sintático: fim de ficheiro inesperado — falta um END?")