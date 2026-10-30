#!/usr/bin/env python3
"""
Gera, a partir de uma única definição do modelo:
  - docs/DER_backupmanager.png  (diagrama, notação pé-de-galinha; requer Graphviz)
  - docs/DER_backupmanager.dot  (fonte do diagrama)
  - docs/DICIONARIO_DE_DADOS.md (dicionário de dados)

Uso:  python3 scripts/gerar_der.py
"""
import json
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
DOCS.mkdir(exist_ok=True)

# (atributo, tipo, chave, descrição)  chave: PK | FK | UQ | ""
MODELO = {
    "USUARIO": ("#4A148C", [
        ("id_usuario", "INT", "PK", "Identificador do usuário"),
        ("nome", "VARCHAR(100)", "", "Nome completo"),
        ("cargo", "VARCHAR(80)", "", "Cargo ou função"),
        ("email", "VARCHAR(120)", "UQ", "E-mail de acesso (único)"),
        ("senha_hash", "VARCHAR(255)", "", "Hash bcrypt da senha"),
        ("perfil_acesso", "ENUM", "", "admin | analista (menor privilégio)"),
        ("tentativas_login", "INT", "", "Tentativas de login malsucedidas (>= 0)"),
        ("bloqueado_ate", "DATETIME", "", "Fim do bloqueio temporário (NULL = sem bloqueio)"),
        ("criado_em", "DATETIME", "", "Data de criação"),
    ]),
    "ATIVO_CRITICO": ("#1565C0", [
        ("id_ativo", "INT", "PK", "Identificador do ativo"),
        ("nome_sistema", "VARCHAR(100)", "UQ", "Nome do servidor/sistema (único)"),
        ("tipo", "VARCHAR(50)", "", "Tipo (banco de dados, aplicação, arquivos...)"),
        ("criticidade", "ENUM", "", "alta | media | baixa"),
        ("responsavel", "VARCHAR(100)", "", "Equipe ou pessoa responsável"),
        ("descricao", "TEXT", "", "Descrição livre"),
        ("rto_meta_min", "INT", "", "Meta de RTO em minutos (> 0)"),
        ("rpo_meta_min", "INT", "", "Meta de RPO em minutos (> 0)"),
        ("criado_em", "DATETIME", "", "Data de cadastro"),
    ]),
    "JOB_BACKUP": ("#1A3A6B", [
        ("id_job", "INT", "PK", "Identificador da execução"),
        ("id_ativo", "INT", "FK", "Ativo protegido -> ATIVO_CRITICO"),
        ("data_execucao", "DATETIME", "", "Data e hora de início"),
        ("tipo_backup", "ENUM", "", "completo | incremental | diferencial"),
        ("status", "ENUM", "", "ok | falha | andamento"),
        ("tamanho_gb", "DECIMAL(10,2)", "", "Volume copiado em GB (>= 0)"),
        ("duracao_min", "INT", "", "Duração em minutos (>= 0)"),
        ("destino", "VARCHAR(100)", "", "Destino da cópia (local ou offsite)"),
    ]),
    "FALHA": ("#B71C1C", [
        ("id_falha", "INT", "PK", "Identificador da falha"),
        ("id_job", "INT", "FK", "Job que falhou -> JOB_BACKUP"),
        ("id_usuario", "INT", "FK", "Quem registrou -> USUARIO"),
        ("data_registro", "DATETIME", "", "Data do registro"),
        ("categoria", "ENUM", "", "timeout_rede | espaco_insuficiente | credencial_expirada | outro"),
        ("descricao_erro", "TEXT", "", "Descrição do erro"),
        ("causa_raiz", "TEXT", "", "Causa raiz identificada"),
        ("encaminhamento", "TEXT", "", "Encaminhamento dado"),
        ("solucao_aplicada", "TEXT", "", "Solução aplicada"),
        ("status_resolucao", "ENUM", "", "aberto | andamento | resolvido"),
        ("data_resolucao", "DATETIME", "", "Preenchida somente se resolvido (CHECK)"),
    ]),
    "RESTAURACAO": ("#1B5E20", [
        ("id_restauracao", "INT", "PK", "Identificador da restauração"),
        ("id_job", "INT", "FK", "Backup restaurado -> JOB_BACKUP"),
        ("id_usuario", "INT", "FK", "Quem solicitou -> USUARIO"),
        ("data_solicitacao", "DATETIME", "", "Início da restauração"),
        ("data_conclusao", "DATETIME", "", "Fim (>= data_solicitacao)"),
        ("motivo", "TEXT", "", "Motivo da restauração"),
        ("rto_realizado_min", "INT", "", "RTO efetivamente realizado (>= 0)"),
        ("resultado", "ENUM", "", "sucesso | parcial | falha"),
    ]),
    "LOG_AUDITORIA": ("#006064", [
        ("id_log", "INT", "PK", "Identificador do registro de auditoria"),
        ("id_usuario", "INT", "FK", "Autor da ação -> USUARIO (NULL se removido)"),
        ("tabela_afetada", "VARCHAR(50)", "", "Tabela alterada"),
        ("acao", "ENUM", "", "INSERT | UPDATE | DELETE"),
        ("id_registro", "INT", "", "Chave do registro afetado"),
        ("data_hora", "DATETIME", "", "Momento da ação"),
    ]),
}

# (pai, filho, rótulo, descrição, regra ao excluir o pai)
RELACOES = [
    ("ATIVO_CRITICO", "JOB_BACKUP", "gera", "1:N", "RESTRICT"),
    ("JOB_BACKUP", "FALHA", "origina", "1:N", "RESTRICT"),
    ("JOB_BACKUP", "RESTAURACAO", "permite", "1:N", "RESTRICT"),
    ("USUARIO", "FALHA", "registra", "1:N", "RESTRICT"),
    ("USUARIO", "RESTAURACAO", "solicita", "1:N", "RESTRICT"),
    ("USUARIO", "LOG_AUDITORIA", "origina", "1:N", "SET NULL"),
]


def no(nome, cor, cols):
    linhas = []
    for a, t, k, _ in cols:
        badge = {"PK": "PK", "FK": "FK", "UQ": "UQ", "": "&nbsp;&nbsp;"}[k]
        bold_a = f"<B>{a}</B>" if k in ("PK", "FK") else a
        linhas.append(
            f'<TR><TD ALIGN="LEFT" WIDTH="26"><FONT COLOR="#555555" POINT-SIZE="10">{badge}</FONT></TD>'
            f'<TD ALIGN="LEFT">{bold_a}</TD><TD ALIGN="LEFT"><FONT COLOR="#666666" POINT-SIZE="10">{t}</FONT></TD></TR>'
        )
    return (
        f'{nome} [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" COLOR="#888888">'
        f'<TR><TD COLSPAN="3" BGCOLOR="{cor}"><FONT COLOR="white"><B>{nome}</B></FONT></TD></TR>'
        + "".join(linhas) + "</TABLE>>];"
    )


def gerar_dot():
    d = ['digraph DER {',
         '  graph [rankdir=LR, splines=spline, nodesep=0.55, ranksep=1.0, bgcolor="white", pad=0.3, fontname="Liberation Sans"];',
         '  node  [shape=plain, fontname="Liberation Sans", fontsize=12];',
         '  edge  [fontname="Liberation Sans", fontsize=11, color="#444444", dir=both, arrowtail=teetee, arrowhead=crowodot, penwidth=1.4];']
    for nome, (cor, cols) in MODELO.items():
        d.append("  " + no(nome, cor, cols))
    for pai, filho, rot, _, _ in RELACOES:
        if pai == "USUARIO" and filho in ("FALHA", "RESTAURACAO"):
            # aresta invertida só para posicionar USUARIO à direita (mantém a notação 1:N)
            d.append(f'  {filho} -> {pai} [label=" {rot} ", dir=both, arrowhead=teetee, arrowtail=crowodot];')
        else:
            d.append(f'  {pai} -> {filho} [label=" {rot} "];')
    d.append("  { rank=same; USUARIO; LOG_AUDITORIA; }")
    d.append("}")
    return "\n".join(d)


def dicionario():
    md = ["# Dicionário de dados — BackupManager", "",
          "Gerado por `scripts/gerar_der.py`. Chaves: **PK** primária, **FK** estrangeira, **UQ** única.", ""]
    for nome, (_, cols) in MODELO.items():
        md += [f"## {nome}", "", "| Atributo | Tipo | Chave | Descrição |", "|---|---|---|---|"]
        md += [f"| `{a}` | {t} | {k or '—'} | {desc} |" for a, t, k, desc in cols]
        md.append("")
    md += ["## Relacionamentos", "", "| Pai | Filho | Verbo | Cardinalidade | Ao excluir o pai |", "|---|---|---|---|---|"]
    md += [f"| {p} | {f} | {r} | {c} | {x} |" for p, f, r, c, x in RELACOES]
    return "\n".join(md) + "\n"


if __name__ == "__main__":
    dot = DOCS / "DER_backupmanager.dot"
    dot.write_text(gerar_dot(), encoding="utf-8")
    subprocess.run(["dot", "-Tpng", "-Gdpi=170", str(dot), "-o", str(DOCS / "DER_backupmanager.png")], check=True)
    (DOCS / "DICIONARIO_DE_DADOS.md").write_text(dicionario(), encoding="utf-8")
    print("Gerados: DER_backupmanager.png/.dot e DICIONARIO_DE_DADOS.md")
