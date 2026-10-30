#!/usr/bin/env python3
"""
Teste rápido (smoke test) dos scripts SQL SEM precisar de um servidor MySQL.

Traduz o dialeto MySQL dos arquivos em database/ para SQLite (ENUM -> CHECK,
AUTO_INCREMENT -> AUTOINCREMENT, remove CREATE DATABASE/USE) e executa:
schema -> seed -> 01..04 e, por fim, as 6 violações de 05_teste_restricoes.sql.

Serve para validar a LÓGICA (restrições, consultas, resultados). A validação
oficial deve ser feita no MySQL 8 (ver README).

Uso:  python3 scripts/validar_sqlite.py [diretorio_de_saida]
"""
import re
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / "database"
SAIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else None
if SAIDA:
    SAIDA.mkdir(parents=True, exist_ok=True)


def traduzir(sql: str) -> str:
    sql = re.sub(r"^\s*(CREATE DATABASE|USE)\b[^;]*;", "", sql, flags=re.M | re.S)
    sql = re.sub(r"\bINT AUTO_INCREMENT PRIMARY KEY\b", "INTEGER PRIMARY KEY AUTOINCREMENT", sql)
    sql = re.sub(r"(\w+)\s+ENUM\(([^)]*)\)", r"\1 TEXT CHECK (\1 IN (\2))", sql)
    return sql


def ler(nome):
    return traduzir((DB / nome).read_text(encoding="utf-8"))


def comandos(sql):
    """Divide o texto em comandos completos (respeita ; dentro de strings)."""
    buf, saida = "", []
    for linha in sql.splitlines(keepends=True):
        if not buf and (not linha.strip() or linha.strip().startswith("--")):
            continue
        buf += linha
        if sqlite3.complete_statement(buf):
            saida.append(buf.strip())
            buf = ""
    return saida


def tabela_mysql(cur):
    cols = [d[0] for d in cur.description]
    linhas = [["NULL" if v is None else str(v) for v in r] for r in cur.fetchall()]
    larg = [max(len(c), *(len(l[i]) for l in linhas)) if linhas else len(c) for i, c in enumerate(cols)]
    sep = "+" + "+".join("-" * (w + 2) for w in larg) + "+"
    fmt = lambda v: "| " + " | ".join(x.ljust(w) for x, w in zip(v, larg)) + " |"
    corpo = [sep, fmt(cols), sep, *(fmt(l) for l in linhas), sep]
    corpo.append(f"{len(linhas)} row{'s' if len(linhas) != 1 else ''} in set")
    return "\n".join(corpo)


con = sqlite3.connect(":memory:")
con.execute("PRAGMA foreign_keys = ON")
cur = con.cursor()


def executar(nome, mostrar=False):
    resultados = []
    for cmd in comandos(ler(nome)):
        cur.execute(cmd)
        if cmd.upper().startswith("SELECT"):
            resultados.append((cmd, tabela_mysql(cur)))
        elif not mostrar:
            pass
    con.commit()
    return resultados


relatorio = []
for arq in ("schema.sql",):
    cur.executescript(ler(arq))
    relatorio.append(f"[ok] {arq}")

seed = RAIZ / "database" / "seed.sql"
if not seed.exists():
    sys.exit("seed.sql nao encontrado: rode  python3 scripts/gerar_seed.py > database/seed.sql")
cur.executescript(ler("seed.sql"))
relatorio.append("[ok] seed.sql")

for arq in ("queries/01_insercao.sql", "queries/02_atualizacao.sql", "queries/03_remocao.sql"):
    cur.executescript(ler(arq))
    relatorio.append(f"[ok] {arq}")

consultas = executar("queries/04_consultas.sql")
relatorio.append(f"[ok] queries/04_consultas.sql ({len(consultas)} consultas)")

# ---- restrições: cada comando deve levantar IntegrityError
falhas_esperadas = 0
resumo_restricoes = []
for i, cmd in enumerate(comandos(ler("queries/05_teste_restricoes.sql")), start=1):
    try:
        cur.execute(cmd)
        resumo_restricoes.append(f"R{i}: NAO FALHOU (inesperado)")
    except sqlite3.IntegrityError as e:
        falhas_esperadas += 1
        resumo_restricoes.append(f"R{i}: bloqueado -> {e}")
con.rollback()
relatorio.append(f"[ok] queries/05_teste_restricoes.sql ({falhas_esperadas}/6 violacoes bloqueadas)")

print("\n".join(relatorio))
print()
for i, (cmd, tab) in enumerate(consultas, start=1):
    print(f"--- C{i} ---\n{tab}\n")
print("--- Restricoes ---")
print("\n".join(resumo_restricoes))

if SAIDA:
    for i, (cmd, tab) in enumerate(consultas, start=1):
        (SAIDA / f"C{i}.txt").write_text(tab + "\n", encoding="utf-8")
    (SAIDA / "restricoes.txt").write_text("\n".join(resumo_restricoes) + "\n", encoding="utf-8")
