# testes.py — Sistema de testes automático
# Lê os ficheiros .f da pasta testes/ e mostra:
#   - Código VM com otimização (para submeter na EWVM)
#   - Código VM sem otimização (para comparação)
#   - Métricas: instruções poupadas

import os
import sys
from main import compilar

SEP = "=" * 68


def _contar(vm: str) -> int:
    """Conta instruções (exclui labels e linhas vazias)."""
    return sum(1 for l in vm.splitlines()
               if l.strip() and not l.strip().endswith(':'))


def correr_teste(nome: str, codigo: str, descricao: str = ''):
    print(f"\n{SEP}")
    print(f"  {nome}")
    if descricao:
        print(f"  Otimização: {descricao}")
    print(SEP)

    vm_com = compilar(codigo, otimizar=True)
    vm_sem = compilar(codigo, otimizar=False)

    if vm_com is None or vm_sem is None:
        print("  [!] Falha na compilação.")
        return

    n_com = _contar(vm_com)
    n_sem = _contar(vm_sem)
    poupadas = n_sem - n_com
    pct = (poupadas / n_sem * 100) if n_sem else 0

    print("\n── CÓDIGO VM (COM otimização) " + "─" * 39)
    for l in vm_com.splitlines():
        print(f"  {l}")

    print("\n── CÓDIGO VM (SEM otimização) " + "─" * 39)
    for l in vm_sem.splitlines():
        print(f"  {l}")

    print(f"\n── MÉTRICAS " + "─" * 56)
    print(f"  SEM otimização : {n_sem} instruções")
    print(f"  COM otimização : {n_com} instruções")
    print(f"  Poupadas       : {poupadas} ({pct:.1f}%)")


def correr_ficheiro(caminho: str):
    """Corre um ficheiro .f como teste."""
    nome = os.path.basename(caminho)
    with open(caminho, encoding='utf-8') as f:
        codigo = f.read()
    correr_teste(nome, codigo)


def correr_pasta(pasta: str):
    """Corre todos os ficheiros .f de uma pasta."""
    ficheiros = sorted(f for f in os.listdir(pasta) if f.endswith('.f'))
    if not ficheiros:
        print(f"Nenhum ficheiro .f encontrado em '{pasta}'.")
        return
    for nome in ficheiros:
        correr_ficheiro(os.path.join(pasta, nome))


# TESTES INLINE (não precisam de ficheiros externos)

TESTES = {
    "Constant Folding": (
        '''
PROGRAM CONSTFOLD
INTEGER X, Y
X = 2 * 3 + 4
Y = X + 0
PRINT *, X
PRINT *, Y
END
''',
        "2*3+4 → pushi 10; X+0 → X"
    ),
    "IF estático": (
        '''
PROGRAM IFSTATICO
INTEGER X
X = 10
IF (.TRUE.) THEN
    PRINT *, 'sempre'
ENDIF
IF (.FALSE.) THEN
    PRINT *, 'nunca'
ENDIF
END
''',
        "IF(.TRUE.) mantido; IF(.FALSE.) eliminado completamente"
    ),
    "De Morgan / NOT": (
        '''
PROGRAM MORGAN
INTEGER A, B
A = 5
B = 3
IF (.NOT. (A .EQ. B)) THEN
    PRINT *, 'diferentes'
ENDIF
END
''',
        "NOT(A .EQ. B) → A .NE. B (elimina instrução NOT)"
    ),
    "Número negativo": (
        '''
PROGRAM NEGATIVO
INTEGER X
X = -5
PRINT *, X
END
''',
        "-5 → pushi -5 direto (sem mul)"
    ),
}


if __name__ == '__main__':
    # Se receber argumento, corre os ficheiros .f dessa pasta
    if len(sys.argv) > 1:
        correr_pasta(sys.argv[1])
    else:
        # Tenta correr a pasta testes/ relativa ao script
        pasta = os.path.join(os.path.dirname(__file__), '..', 'testes')
        if os.path.isdir(pasta):
            print("A correr ficheiros da pasta testes/...")
            correr_pasta(pasta)

        # E também os testes inline de otimização
        print(f"\n\n{'#'*68}")
        print("  TESTES DE OTIMIZAÇÃO")
        print('#'*68)
        for nome, (codigo, desc) in TESTES.items():
            correr_teste(nome, codigo, desc)

    print(f"\n{SEP}")
    print("  CONCLUÍDO")
    print(SEP)