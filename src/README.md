# Compilador Fortran 77 → EWVM

Compilador desenvolvido em Python com PLY (`ply.lex` + `ply.yacc`) que traduz programas **Fortran 77** para código assembly da máquina virtual **EWVM** (European Web Virtual Machine).

---

## Pré-requisitos

- Python 3.10+
- Biblioteca PLY:
  ```bash
  pip install ply
  ```

---

## Estrutura da pasta `src/`

```
src/
├── main.py          # Ponto de entrada do compilador
├── lexer.py         # Análise léxica (ply.lex)
├── parser.py        # Análise sintática (ply.yacc)
├── semantic.py      # Análise semântica
├── otimizador.py    # Otimizações sobre a AST
├── codegen.py       # Geração de código EWVM
├── testes.py        # Suite de testes com métricas de otimização
└── output/          # Pasta criada automaticamente com os ficheiros .vm gerados
```

---

## Utilização

Todos os comandos devem ser executados **dentro da pasta `src/`**:

```bash
cd src/
```

### 1. Compilar um ficheiro Fortran

Imprime o código EWVM gerado no terminal:

```bash
python main.py ../testes/exemplo1.f
```

### 2. Compilar todos os exemplos de uma vez

Sem argumentos, o compilador percorre todos os ficheiros `.f` da pasta `../testes/`, compila cada um e guarda os resultados em `src/output/`:

```bash
python main.py
```

Os ficheiros gerados ficam em `src/output/output_1.vm`, `output_2.vm`, etc.

### 3. Correr a suite de testes com métricas

```bash
python testes.py
```

Compila cada exemplo com e sem otimização e apresenta o número de instruções geradas e a percentagem de redução obtida.

---

## Exemplos de output

Para o programa `exemplo1.f` (Olá Mundo):

```fortran
PROGRAM HELLO
PRINT *, 'Ola, Mundo!'
END
```

O compilador gera:

```
pushi 0
start
pushs "Ola, Mundo!"
writes
writeln
stop
```

---

## Fases do compilador

| Fase | Ficheiro | Descrição |
|------|----------|-----------|
| Análise Léxica | `lexer.py` | Tokenização com `ply.lex`; trata comentários `C`-coluna-1, case-insensitivity e operadores Fortran (`.AND.`, `.EQ.`, etc.) |
| Análise Sintática | `parser.py` | Gramática com `ply.yacc`; constrói AST em tuplos Python |
| Análise Semântica | `semantic.py` | Verifica variáveis declaradas, labels de `DO`/`GOTO` e assinaturas de subprogramas |
| Otimização | `otimizador.py` | Constant folding, álgebra simples, IF estático, leis de De Morgan, entre outras |
| Geração de Código | `codegen.py` | Duas passagens: alocação de memória e emissão de instruções EWVM |
