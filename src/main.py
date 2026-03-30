from parser import Parser
from semantic import SemanticAnalyzer
from codegen import CodeGenerator
from otimizador import Otimizador
from lexer import Lexer


def compilar(codigo_fonte):
    print("=" * 50)
    print(" INÍCIO DA COMPILAÇÃO")
    print("=" * 50)

    # 1. FASE SINTÁTICA (que já chama o lexer automaticamente)
    print("\n[1/3] A executar Análise Sintática...")
    meu_lexer = Lexer()
    meu_parser = Parser()
    codigo_fonte = meu_lexer.preprocessar(codigo_fonte)
    ast = meu_parser.parse(codigo_fonte, lexer=meu_lexer.lexer)

    if not ast:
        print("\n[!] Erro Crítico: A compilação falhou na fase sintática. Abortando.")
        return

    print(" -> Árvore gerada com sucesso!")

    # 2. FASE SEMÂNTICA
    print("\n[2/3] A executar Análise Semântica (Verificação de Variáveis)...")
    analisador = SemanticAnalyzer()
    analisador.analyze(ast)
    analisador.verify_labels()

    # Se a lista de erros não estiver vazia, falhamos a compilação
    if analisador.errors:
        print("\n[!] Falha na Compilação! Foram encontrados Erros Semânticos:")
        for erro in analisador.errors:
            print(f"    - {erro}")
        return
    else:
        print(" -> Sucesso! Variáveis e tipos coerentes.")
        print(" -> Tabela de Símbolos final:", analisador.symbol_table)

    # 3. FASE DE GERAÇÃO DE CÓDIGO
    print("\n[+] A executar Otimização de Código (Constant Folding)...")
    otimizador = Otimizador()
    ast_otimizada = otimizador.optimize(ast)
    print(" -> AST otimizada com sucesso. Expressões constantes reduzidas.")
    print("\n[3/3] A gerar Código de Máquina (EWVM)...")

    gerador = CodeGenerator()
    gerador.scan_memory(ast_otimizada)
    gerador.generate(ast_otimizada)

    print("\n" + "=" * 50)
    print(" CÓDIGO GERADO COM SUCESSO (Copia e Cola na EWVM)")
    print("=" * 50 + "\n")

    codigo_vm = "\n".join(gerador.code)
    print(codigo_vm)

    print("\n" + "=" * 50)


# ZONA DE TESTE DO COMPILADOR COMPLETO
if __name__ == '__main__':
    exemplos = {
        "1. Teste 1": '''
                PROGRAM HELLO
                PRINT *, 'Ola, Mundo!'
                END
                ''',
        "2. Teste 2": '''
            PROGRAM FATORIAL
            INTEGER N, I, FAT
            PRINT *, 'Introduza um numero inteiro positivo:'
            READ *, N
            FAT = 1
            DO 10 I = 1, N
                FAT = FAT * I
            10 CONTINUE
            PRINT *, 'Fatorial de ', N, ': ', FAT
            END
            ''',
        "3. Teste 3": '''
                PROGRAM PRIMO
                INTEGER NUM, I
                LOGICAL ISPRIM
                PRINT *, 'Introduza um numero inteiro positivo:'
                READ *, NUM
                ISPRIM = .TRUE.
                I = 2
                20 IF (I .LE. (NUM/2) .AND. ISPRIM) THEN
                        IF (MOD(NUM, I) .EQ. 0) THEN
                            ISPRIM = .FALSE.
                        ENDIF
                        I = I + 1
                        GOTO 20
                ENDIF
                IF (ISPRIM) THEN
                    PRINT *, NUM, ' e um numero primo'
                ELSE
                    PRINT *, NUM, ' nao e um numero primo'
                ENDIF
                END
                ''',
        "4. Teste 4": '''
            PROGRAM SOMAARR
            INTEGER NUMS(5)
            INTEGER I, SOMA
            SOMA = 0
            PRINT *, 'Introduza 5 numeros inteiros:'
            DO 30 I = 1, 5
                READ *, NUMS(I)
                SOMA = SOMA + NUMS(I)
            30 CONTINUE
            PRINT *, 'A soma dos numeros e: ', SOMA
            END
            ''',
        "5. Teste 5": '''
            PROGRAM CONVERSOR
            INTEGER NUM, BASE, RESULT, CONVRT
            
            PRINT *, 'INTRODUZA UM NUMERO DECIMAL INTEIRO:'
            READ *, NUM
            
            DO 10 BASE = 2, 9
                RESULT = CONVRT(NUM, BASE)
                PRINT *, 'BASE ', BASE, ': ', RESULT
            10 CONTINUE
            
            END
            
            INTEGER FUNCTION CONVRT(N, B)
            INTEGER N, B, QUOT, REM, POT, VAL
            VAL = 0
            POT = 1
            QUOT = N
            20 IF (QUOT .GT. 0) THEN
                REM = MOD(QUOT, B)
                VAL = VAL + (REM * POT)
                QUOT = QUOT / B
                POT = POT * 10
                GOTO 20
            ENDIF
            CONVRT = VAL
            RETURN
            END
            '''
    }

    for nome, codigo in exemplos.items():
        print(f"\n\n>>> A TESTAR: {nome}")
        compilar(codigo)