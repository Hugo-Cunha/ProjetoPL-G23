from parser import parser
from semantic import SemanticAnalyzer
from codegen import CodeGenerator

def compilar(codigo_fonte):
    print("=" * 50)
    print(" INÍCIO DA COMPILAÇÃO")
    print("=" * 50)

    # 1. FASE SINTÁTICA (que já chama o lexer automaticamente)
    print("\n[1/3] A executar Análise Sintática...")
    ast = parser.parse(codigo_fonte)

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

    # 3. FASE DE GERAÇÃO DE CÓDIGO (Futuro)
    print("\n[3/3] A gerar Código de Máquina (EWVM)...")

    # Criamos o gerador de código passando as variáveis validadas
    gerador = CodeGenerator(analisador.symbol_table)
    gerador.generate(ast)

    print("\n" + "=" * 50)
    print(" CÓDIGO GERADO COM SUCESSO (Copia e Cola na EWVM)")
    print("=" * 50 + "\n")

    # Junta todas as instruções separadas por quebras de linha e imprime!
    codigo_vm = "\n".join(gerador.code)
    print(codigo_vm)

    print("\n" + "=" * 50)


# ==========================================
# ZONA DE TESTE DO COMPILADOR COMPLETO
# ==========================================
if __name__ == '__main__':
    # O teste final sem erros para testarmos o Fatorial na VM!
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
    compilar(codigo_teste)