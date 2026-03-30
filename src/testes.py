# testes.py
# Sistema de testes do compilador Fortran 77 → EWVM
#
# Para cada teste mostra:
#   - O código Fortran fonte

#   - O código VM gerado COM otimizações

#   - O código VM gerado SEM otimizações (para comparação)

#   - Métricas: nº de instruções poupadas, quais instruções mudaram

from parser import parser
from semantic import SemanticAnalyzer
from codegen import CodeGenerator
from otimizador import Otimizador
from lexer import preprocessar

# MOTOR DE COMPILAÇÃO

def compilar(codigo_fonte, otimizar=True, verbose=False):
    """
    Compila código Fortran 77 para EWVM.
    Retorna (codigo_vm: str, sucesso: bool).
    otimizar=False → salta a fase de otimização (para comparação).
    """
    codigo = preprocessar(codigo_fonte)
    ast = parser.parse(codigo)
    if not ast:
        return None, False

    analisador = SemanticAnalyzer()
    analisador.analyze(ast)
    analisador.verify_labels()
    if analisador.errors:
        if verbose:
            for e in analisador.errors:
                print(f"  [!] {e}")
        return None, False

    if otimizar:
        ast = Otimizador().optimize(ast)

    gerador = CodeGenerator()
    gerador.scan_memory(ast)
    gerador.generate(ast)
    return "\n".join(gerador.code), True


def contar_instrucoes(codigo_vm):
    """Conta instruções reais (ignora labels e linhas vazias)."""
    if not codigo_vm:
        return 0
    return sum(
        1 for linha in codigo_vm.splitlines()
        if linha.strip() and not linha.strip().endswith(':')
    )


def diff_instrucoes(sem_opt, com_opt):
    """Devolve as linhas que existem em sem_opt mas não em com_opt."""
    s = set(sem_opt.splitlines())
    c = set(com_opt.splitlines())
    return sorted(s - c)


# INFRA DE APRESENTAÇÃO

SEP  = "=" * 70
SEP2 = "-" * 70

def cabecalho(titulo):
    print(f"\n{SEP}")
    print(f"  {titulo}")
    print(SEP)

def mostrar_vm(titulo, codigo):
    print(f"\n{'─'*4} {titulo} {'─'*(60-len(titulo))}")
    if codigo:
        for linha in codigo.splitlines():
            print(f"  {linha}")
    else:
        print("  (sem código)")

def mostrar_metricas(n_sem, n_com, instruções_removidas):
    poupadas = n_sem - n_com
    pct = (poupadas / n_sem * 100) if n_sem > 0 else 0
    print(f"\n{'─'*4} MÉTRICAS {'─'*57}")
    print(f"  Instruções SEM otimização : {n_sem}")
    print(f"  Instruções COM otimização : {n_com}")
    print(f"  Instruções poupadas       : {poupadas} ({pct:.1f}%)")
    if instruções_removidas:
        print(f"  Padrões eliminados        :")
        for i in instruções_removidas[:8]:  # mostra até 8
            print(f"    - {i.strip()}")


def correr_teste(nome, codigo_fortran, descricao_otimizacao=""):
    cabecalho(f"TESTE: {nome}")
    if descricao_otimizacao:
        print(f"  Otimização demonstrada: {descricao_otimizacao}")
    print(f"\n  Código Fortran:")
    for linha in codigo_fortran.strip().splitlines():
        print(f"    {linha}")

    vm_com,  ok1 = compilar(codigo_fortran, otimizar=True)
    vm_sem,  ok2 = compilar(codigo_fortran, otimizar=False)

    if not ok1 or not ok2:
        print("\n  [!] Falha na compilação — ver erros acima.")
        return

    n_com = contar_instrucoes(vm_com)
    n_sem = contar_instrucoes(vm_sem)
    removidas = diff_instrucoes(vm_sem, vm_com)

    mostrar_vm("CÓDIGO VM — COM otimização (submeter na EWVM)", vm_com)
    mostrar_vm("CÓDIGO VM — SEM otimização (referência)", vm_sem)
    mostrar_metricas(n_sem, n_com, removidas)


# TESTES

# ── Teste 1: Olá Mundo ────────────────────────────────────────────────────────
T1 = '''
PROGRAM HELLO
PRINT *, 'Ola, Mundo!'
END
'''

# ── Teste 2: Fatorial (DO loop) ───────────────────────────────────────────────
T2 = '''
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
'''

# ── Teste 3: É primo? (padrão WHILE = labeled IF + GOTO) ─────────────────────
T3 = '''
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
'''

# ── Teste 4: Soma de array ────────────────────────────────────────────────────
T4 = '''
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
'''

# ── Teste 5: Conversor de bases (função + padrão WHILE) ───────────────────────
T5 = '''
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

# ── Teste 6: Constant Folding ─────────────────────────────────────────────────
# Expressões com constantes que o otimizador deve calcular em compile-time
T6 = '''
PROGRAM CONSTFOLD
INTEGER X, Y
X = 2 * 3 + 4
Y = X + 0
PRINT *, X
PRINT *, Y
END
'''

# ── Teste 7: IF estático (.TRUE./.FALSE.) ─────────────────────────────────────
T7 = '''
PROGRAM IFSTATICO
INTEGER X
X = 10
IF (.TRUE.) THEN
    PRINT *, 'sempre entra aqui'
ENDIF
IF (.FALSE.) THEN
    PRINT *, 'nunca chega aqui'
ENDIF
END
'''

# ── Teste 8: Comentários (lexer) ──────────────────────────────────────────────
T8 = '''
C Este e um comentario estilo Fortran 77
PROGRAM COMENTARIOS
INTEGER X
C Outro comentario
X = 42 ! comentario inline
PRINT *, X ! imprime o valor
END
'''

# ── Teste 9: Numero negativo (UMINUS) ─────────────────────────────────────────
T9 = '''
PROGRAM NEGATIVO
INTEGER X, Y
X = -5
Y = X * -1
PRINT *, Y
END
'''

# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == '__main__':
    correr_teste(
        "1 — Olá Mundo",
        T1,
        "Nenhuma (teste base)"
    )
    correr_teste(
        "2 — Fatorial com DO loop",
        T2,
        "Nenhuma (ciclo DO com label)"
    )
    correr_teste(
        "3 — Número primo (WHILE pattern)",
        T3,
        "Deteção do padrão labeled-IF+GOTO → ciclo while estruturado"
    )
    correr_teste(
        "4 — Soma de array",
        T4,
        "Nenhuma (teste de arrays)"
    )
    correr_teste(
        "5 — Conversor de bases (função + WHILE pattern)",
        T5,
        "Deteção do padrão WHILE na função CONVRT"
    )
    correr_teste(
        "6 — Constant Folding",
        T6,
        "Expressões constantes calculadas em compile-time (ex: 2*3+4 → 10)"
    )
    correr_teste(
        "7 — IF com condição estática",
        T7,
        "IF(.TRUE.) e IF(.FALSE.) eliminados em compile-time"
    )
    correr_teste(
        "8 — Comentários Fortran 77",
        T8,
        "Lexer: C na coluna 1 e ! inline ignorados corretamente"
    )
    correr_teste(
        "9 — Número negativo (UMINUS)",
        T9,
        "Minus unário: -5 e --X reconhecidos e otimizados"
    )

    print(f"\n{SEP}")
    print("  TODOS OS TESTES CONCLUÍDOS")
    print(SEP)