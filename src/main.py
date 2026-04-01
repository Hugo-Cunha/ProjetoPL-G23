# main.py — Ponto de entrada do compilador Fortran 77 → EWVM
#
# Uso:
#   python main.py ficheiro.f          → compila e imprime o código VM
#   python main.py ficheiro.f -o out   → guarda o código VM em 'out'
#   python main.py                     → corre os exemplos internos

import sys
import os
from lexer      import Lexer
from parser     import Parser
from semantic   import SemanticAnalyzer
from otimizador import Otimizador
from codegen    import CodeGenerator


def compilar(codigo_fonte: str, otimizar: bool = True) -> str | None:
    """
    Compila código Fortran 77 para EWVM.
    Retorna o código VM como string, ou None se houver erros.
    """
    # Fase 1: Análise Léxica + Sintática
    lexer  = Lexer()
    parser = Parser()
    codigo = lexer.preprocessar(codigo_fonte)
    ast    = parser.parse(codigo, lexer=lexer.lexer)

    if ast is None:
        print("[!] Erro: falha na análise sintática.")
        return None

    # Fase 2: Análise Semântica
    sem = SemanticAnalyzer()
    sem.analyze(ast)
    print(ast)

    if sem.errors:
        print("[!] Erros semânticos encontrados:")
        for err in sem.errors:
            print(f"    • {err}")
        return None

    # Fase 3: Otimização
    if otimizar:
        ast = Otimizador().optimize(ast)

    # Fase 4: Geração de Código
    gen = CodeGenerator()
    gen.scan_memory(ast)
    gen.generate(ast)
    return "\n".join(gen.code)


def compilar_ficheiro(caminho: str, otimizar: bool = True) -> str | None:
    """Lê um ficheiro .f e compila-o."""
    if not os.path.exists(caminho):
        print(f"[!] Ficheiro não encontrado: {caminho}")
        return None
    with open(caminho, encoding='utf-8') as f:
        return compilar(f.read(), otimizar=otimizar)


# CLI

def _cli():
    args = sys.argv[1:]
    if not args:
        _demo()
        return

    ficheiro = args[0]
    saida    = args[args.index('-o') + 1] if '-o' in args else None
    otimizar = '--no-opt' not in args

    codigo_vm = compilar_ficheiro(ficheiro, otimizar=otimizar)
    if codigo_vm is None:
        sys.exit(1)

    if saida:
        with open(saida, 'w', encoding='utf-8') as f:
            f.write(codigo_vm)
        print(f"Código VM guardado em '{saida}'.")
    else:
        print(codigo_vm)


def _demo():
    """Compila os exemplos da pasta testes/ se existirem, senão usa exemplos inline."""
    testes_dir = os.path.join(os.path.dirname(__file__), '..', 'testes')
    ficheiros  = sorted(f for f in os.listdir(testes_dir) if f.endswith('.f')) \
                 if os.path.isdir(testes_dir) else []

    if ficheiros:
        for nome in ficheiros:
            caminho = os.path.join(testes_dir, nome)
            print(f"\n{'='*60}")
            print(f"  {nome}")
            print('='*60)
            vm = compilar_ficheiro(caminho)
            if vm:
                print(vm)
    else:
        print("Sem ficheiros de teste. Usa: python main.py ficheiro.f")


if __name__ == '__main__':
    _cli()