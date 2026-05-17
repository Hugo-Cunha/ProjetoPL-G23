# Compilador Fortran 77 → EWVM

Compilador desenvolvido no âmbito da unidade curricular de **Processamento de Linguagens** (2026), que traduz programas escritos em **Fortran 77** (standard ANSI X3.9-1978) para código assembly da máquina virtual **EWVM** (European Web Virtual Machine).

---

## Grupo 23

| Número | Nome |
|--------|------|
| A107324 | David José Barbosa Alves |
| A107368 | Diogo Malheiro Pais |
| A106808 | Hugo Araújo Cunha |

---

## Funcionalidades

- Análise léxica com `ply.lex` — tokenização com suporte a comentários Fortran (`C` na coluna 1), *case-insensitivity* e operadores `.AND.`, `.EQ.`, etc.
- Análise sintática com `ply.yacc` — construção de AST com suporte a `IF/THEN/ELSE`, ciclos `DO`, `GOTO`, `READ`, `PRINT`, `FUNCTION` e `SUBROUTINE`
- Análise semântica — verificação de variáveis declaradas, consistência de labels `DO`/`GOTO` e assinaturas de subprogramas
- Otimização de código — *constant folding*, simplificação algébrica, IF estático, leis de De Morgan, entre outras
- Geração de código EWVM — duas passagens (alocação de memória + emissão de instruções)

---

## Estrutura do Repositório

```
ProjetoPL-G23/
├── src/
│   ├── main.py          # Ponto de entrada do compilador
│   ├── lexer.py         # Análise léxica
│   ├── parser.py        # Análise sintática
│   ├── semantic.py      # Análise semântica
│   ├── otimizador.py    # Otimizações sobre a AST
│   ├── codegen.py       # Geração de código EWVM
│   ├── testes.py        # Suite de testes com métricas de otimização
│   └── README.md        # Instruções detalhadas de uso
├── testes/
│   ├── exemplo1.f       # Olá Mundo
│   ├── exemplo2.f       # Fatorial
│   ├── exemplo3.f       # Número primo
│   ├── exemplo4.f       # Soma de array
│   └── exemplo5.f       # Conversor de bases (com função)
└── doc/
    └── Relatorio_PL.md  # Relatório técnico do projeto
```

---

## Instalação e Uso Rápido

**Pré-requisito:** Python 3.10+ e a biblioteca PLY.

```bash
pip install ply
cd src/
```

| Objetivo | Comando |
|----------|---------|
| Compilar um ficheiro e ver o output | `python main.py ../testes/exemplo1.f` |
| Guardar o código VM num ficheiro | `python main.py ../testes/exemplo1.f -o output/exemplo1.vm` |
| Compilar todos os exemplos de uma vez | `python main.py` |
| Compilar sem otimizações | `python main.py ../testes/exemplo1.f --no-opt` |
| Correr testes com métricas | `python testes.py` |

Para instruções mais detalhadas, incluindo como adicionar novos programas de teste, consulte [`src/README.md`](src/README.md).

---

## Documentação

O relatório técnico com a descrição completa da implementação, gramática utilizada, otimizações aplicadas e resultados dos testes está disponível em [`doc/Relatorio_PL.md`](doc/Relatorio_PL.md).