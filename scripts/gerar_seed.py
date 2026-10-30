#!/usr/bin/env python3
"""
Gera database/seed.sql com DADOS SINTÉTICOS para o BackupManager.

Os dados reproduzem apenas o PERFIL estatístico dos logs analisados na ação de
extensão (847 jobs em 28 dias; 48 falhas: 18 timeout de rede, 15 espaço
insuficiente, 15 credencial expirada). Nenhum dado real de empresa ou de
cidadão é versionado neste repositório.

Uso:  python3 scripts/gerar_seed.py > database/seed.sql
"""
import random
from datetime import datetime, timedelta

rng = random.Random(2026)          # semente fixa => saída idêntica a cada execução
INICIO = datetime(2026, 4, 1)
DIAS = 28

def q(v):
    """Escapa literal SQL."""
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, datetime):
        return "'" + v.strftime("%Y-%m-%d %H:%M:%S") + "'"
    return "'" + str(v).replace("'", "''") + "'"

def insert(tabela, colunas, linhas, bloco=100):
    out = []
    for i in range(0, len(linhas), bloco):
        parte = linhas[i:i + bloco]
        vals = ",\n  ".join("(" + ", ".join(q(c) for c in l) + ")" for l in parte)
        out.append(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES\n  {vals};")
    return "\n".join(out)

HASH = "$2b$10$SUBSTITUIR.PELO.HASH.BCRYPT.GERADO.PELA.APLICACAO"

# ----------------------------------------------------------------- usuários
usuarios = [
    (1, "Administrador do Sistema", "Coordenação de TI", "admin@backupmanager.local", HASH, "admin", 0, None, datetime(2026, 3, 30, 9, 0)),
    (2, "Analista de Infraestrutura", "Analista de TI", "infra@backupmanager.local", HASH, "analista", 0, None, datetime(2026, 3, 30, 9, 5)),
    (3, "Analista de Segurança da Informação", "Analista de SI", "seguranca@backupmanager.local", HASH, "analista", 0, None, datetime(2026, 3, 30, 9, 10)),
]

# ------------------------------------------------------------------- ativos
# metas (min): alta 4h/4h | média 8h/24h | baixa 24h/72h
META = {"alta": (240, 240), "media": (480, 1440), "baixa": (1440, 4320)}
ativos_def = [
    (1, "SRV-DB-01",   "Servidor de Banco de Dados", "alta",  "Equipe de Banco de Dados", "Banco principal MySQL (cadastros e transações)", 200, 120.0),
    (2, "SRV-DB-02",   "Servidor de Banco de Dados", "alta",  "Equipe de Banco de Dados", "Réplica e base de relatórios",                    180, 95.0),
    (3, "SRV-APP-02",  "Servidor de Aplicação",      "media", "Equipe de Infraestrutura", "Aplicação web interna",                           180, 40.0),
    (4, "SRV-FILE-01", "Servidor de Arquivos",       "media", "Equipe de Infraestrutura", "Compartilhamentos departamentais",                157, 150.0),
    (5, "SRV-MAIL-01", "Servidor de E-mail",         "baixa", "Equipe de Infraestrutura", "Caixas de e-mail institucionais",                 130, 60.0),
]
ativos = [(i, n, t, c, r, d, *META[c], datetime(2026, 3, 30, 10, 0)) for i, n, t, c, r, d, _, _ in ativos_def]

# --------------------------------------------------------------------- jobs
jobs = []          # (id, ativo, data, tipo, status, gb, dur, destino)
job_id = 0
por_ativo = {}     # ativo -> lista de índices em `jobs`
for ativo_id, _, _, _, _, _, njobs, base_gb in ativos_def:
    por_ativo[ativo_id] = []
    for k in range(njobs):
        job_id += 1
        dia = (k * DIAS) // njobs
        hora = 1 + (k % 3)                      # janelas de 01h, 02h e 03h
        data = INICIO + timedelta(days=dia, hours=hora, minutes=rng.choice([0, 0, 5, 10, 15]))
        tipo = "completo" if k % 7 == 0 else ("diferencial" if k % 7 == 3 else "incremental")
        fator = {"completo": 1.0, "diferencial": 0.22, "incremental": 0.08}[tipo]
        gb = round(base_gb * fator * rng.uniform(0.85, 1.15), 2)
        dur = max(2, int(gb * 0.39))
        destino = "DISCO-LOCAL" if k % 2 == 0 else "NUVEM-OFFSITE"
        jobs.append([job_id, ativo_id, data, tipo, "ok", gb, dur, destino])
        por_ativo[ativo_id].append(len(jobs) - 1)

# ------------------------------------------------- falhas (48 = 18 + 15 + 15)
PLANO = [  # (categoria, ativo, quantidade)
    ("timeout_rede", 4, 9), ("timeout_rede", 3, 9),
    ("espaco_insuficiente", 1, 8), ("espaco_insuficiente", 4, 7),
    ("credencial_expirada", 2, 8), ("credencial_expirada", 5, 7),
]
TEXTOS = {
    "timeout_rede": ("Job interrompido por timeout de rede (ERR_TIMEOUT).",
                     "Instabilidade no enlace entre o servidor e o destino do backup.",
                     "Equipe de redes acionada para análise do enlace.",
                     "Janela de backup reagendada e timeout do agente ajustado."),
    "espaco_insuficiente": ("Job abortado: espaço insuficiente no volume de destino.",
                            "Retenção acima do dimensionamento do volume.",
                            "Revisão da política de retenção solicitada.",
                            "Backups expirados removidos e volume ampliado."),
    "credencial_expirada": ("Falha de autenticação do agente (AUTH_ERR).",
                            "Senha da conta de serviço expirou sem aviso.",
                            "Renovação da credencial solicitada à segurança.",
                            "Credencial renovada e rotina de alerta de expiração criada."),
}
falhas_jobs = []   # (idx_job, categoria)
for cat, ativo, n in PLANO:
    for idx in rng.sample(por_ativo[ativo], n):
        falhas_jobs.append((idx, cat))

for idx, _ in falhas_jobs:
    jobs[idx][4] = "falha"      # status
    jobs[idx][5] = 0.0          # tamanho_gb
    jobs[idx][6] = rng.randint(2, 12)

# 12 falhas em aberto: DB-01 (5), DB-02 (3), FILE-01 (4) — as mais recentes de cada ativo
QUOTA_ABERTO = {1: 5, 2: 3, 4: 4}
ordenadas = sorted(falhas_jobs, key=lambda f: jobs[f[0]][2], reverse=True)
abertas, restantes = [], []
cont = dict.fromkeys(QUOTA_ABERTO, 0)
for f in ordenadas:
    a = jobs[f[0]][1]
    if a in QUOTA_ABERTO and cont[a] < QUOTA_ABERTO[a]:
        cont[a] += 1
        abertas.append(f)
    else:
        restantes.append(f)
andamento = restantes[:6]                    # 6 mais recentes das demais
resolvidas = restantes[6:]                   # 30 resolvidas

falhas, logs = [], []
fid = 0
for lista, status in ((resolvidas, "resolvido"), (andamento, "andamento"), (abertas, "aberto")):
    for idx, cat in sorted(lista, key=lambda f: jobs[f[0]][2]):
        fid += 1
        desc, causa, enc, sol = TEXTOS[cat]
        reg = jobs[idx][2] + timedelta(hours=1)
        usuario = rng.choice([2, 3])
        if status == "resolvido":
            res = reg + timedelta(hours=rng.randint(2, 30))
            falhas.append((fid, jobs[idx][0], usuario, reg, cat, desc, causa, enc, sol, status, res))
            logs.append((usuario, "FALHA", "UPDATE", fid, res))
        elif status == "andamento":
            falhas.append((fid, jobs[idx][0], usuario, reg, cat, desc, causa, enc, None, status, None))
        else:
            falhas.append((fid, jobs[idx][0], usuario, reg, cat, desc, None, None, None, status, None))
        logs.append((usuario, "FALHA", "INSERT", fid, reg))

# ------------------------------------------------- restaurações (RTO médio 21)
RTOS = [12, 18, 32, 25, 14, 20, 28, 17, 22, 22]
MOTIVOS = ["Teste periódico de restauração", "Recuperação de arquivo excluído acidentalmente",
           "Validação de integridade do backup completo", "Simulação de desastre (DR)"]
ok_jobs = [j for j in jobs if j[4] == "ok" and j[3] == "completo"]
escolhidos = rng.sample(ok_jobs, len(RTOS))
restauracoes = []
for rid, (j, rto) in enumerate(zip(escolhidos, RTOS), start=1):
    sol = j[2] + timedelta(days=2, hours=9, minutes=rng.choice([0, 15, 30]))
    concl = sol + timedelta(minutes=rto)
    usuario = rng.choice([2, 3])
    resultado = "parcial" if rid == 7 else "sucesso"
    restauracoes.append((rid, j[0], usuario, sol, concl, rng.choice(MOTIVOS), rto, resultado))
    logs.append((usuario, "RESTAURACAO", "INSERT", rid, sol))

logs.sort(key=lambda l: l[4])
logs_sql = [(i, u, t, a, r, d) for i, (u, t, a, r, d) in enumerate(logs, start=1)]

# ------------------------------------------------------------------- saída
print("-- =====================================================================")
print("-- BackupManager — Dados SINTÉTICOS de teste (gerado por scripts/gerar_seed.py)")
print("-- Execução: mysql -u root -p backupmanager < database/seed.sql")
print("-- ATENÇÃO: senha_hash é um marcador; gere hashes bcrypt reais antes de usar.")
print("-- =====================================================================")
print("USE backupmanager;\n")
print(insert("USUARIO", ["id_usuario", "nome", "cargo", "email", "senha_hash", "perfil_acesso", "tentativas_login", "bloqueado_ate", "criado_em"], usuarios), "\n")
print(insert("ATIVO_CRITICO", ["id_ativo", "nome_sistema", "tipo", "criticidade", "responsavel", "descricao", "rto_meta_min", "rpo_meta_min", "criado_em"], ativos), "\n")
print(insert("JOB_BACKUP", ["id_job", "id_ativo", "data_execucao", "tipo_backup", "status", "tamanho_gb", "duracao_min", "destino"], [tuple(j) for j in jobs]), "\n")
print(insert("FALHA", ["id_falha", "id_job", "id_usuario", "data_registro", "categoria", "descricao_erro", "causa_raiz", "encaminhamento", "solucao_aplicada", "status_resolucao", "data_resolucao"], falhas), "\n")
print(insert("RESTAURACAO", ["id_restauracao", "id_job", "id_usuario", "data_solicitacao", "data_conclusao", "motivo", "rto_realizado_min", "resultado"], restauracoes), "\n")
print(insert("LOG_AUDITORIA", ["id_log", "id_usuario", "tabela_afetada", "acao", "id_registro", "data_hora"], logs_sql))
