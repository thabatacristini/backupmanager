# Dicionário de dados — BackupManager

Gerado por `scripts/gerar_der.py`. Chaves: **PK** primária, **FK** estrangeira, **UQ** única.

## USUARIO

| Atributo | Tipo | Chave | Descrição |
|---|---|---|---|
| `id_usuario` | INT | PK | Identificador do usuário |
| `nome` | VARCHAR(100) | — | Nome completo |
| `cargo` | VARCHAR(80) | — | Cargo ou função |
| `email` | VARCHAR(120) | UQ | E-mail de acesso (único) |
| `senha_hash` | VARCHAR(255) | — | Hash bcrypt da senha |
| `perfil_acesso` | ENUM | — | admin | analista (menor privilégio) |
| `tentativas_login` | INT | — | Tentativas de login malsucedidas (>= 0) |
| `bloqueado_ate` | DATETIME | — | Fim do bloqueio temporário (NULL = sem bloqueio) |
| `criado_em` | DATETIME | — | Data de criação |

## ATIVO_CRITICO

| Atributo | Tipo | Chave | Descrição |
|---|---|---|---|
| `id_ativo` | INT | PK | Identificador do ativo |
| `nome_sistema` | VARCHAR(100) | UQ | Nome do servidor/sistema (único) |
| `tipo` | VARCHAR(50) | — | Tipo (banco de dados, aplicação, arquivos...) |
| `criticidade` | ENUM | — | alta | media | baixa |
| `responsavel` | VARCHAR(100) | — | Equipe ou pessoa responsável |
| `descricao` | TEXT | — | Descrição livre |
| `rto_meta_min` | INT | — | Meta de RTO em minutos (> 0) |
| `rpo_meta_min` | INT | — | Meta de RPO em minutos (> 0) |
| `criado_em` | DATETIME | — | Data de cadastro |

## JOB_BACKUP

| Atributo | Tipo | Chave | Descrição |
|---|---|---|---|
| `id_job` | INT | PK | Identificador da execução |
| `id_ativo` | INT | FK | Ativo protegido -> ATIVO_CRITICO |
| `data_execucao` | DATETIME | — | Data e hora de início |
| `tipo_backup` | ENUM | — | completo | incremental | diferencial |
| `status` | ENUM | — | ok | falha | andamento |
| `tamanho_gb` | DECIMAL(10,2) | — | Volume copiado em GB (>= 0) |
| `duracao_min` | INT | — | Duração em minutos (>= 0) |
| `destino` | VARCHAR(100) | — | Destino da cópia (local ou offsite) |

## FALHA

| Atributo | Tipo | Chave | Descrição |
|---|---|---|---|
| `id_falha` | INT | PK | Identificador da falha |
| `id_job` | INT | FK | Job que falhou -> JOB_BACKUP |
| `id_usuario` | INT | FK | Quem registrou -> USUARIO |
| `data_registro` | DATETIME | — | Data do registro |
| `categoria` | ENUM | — | timeout_rede | espaco_insuficiente | credencial_expirada | outro |
| `descricao_erro` | TEXT | — | Descrição do erro |
| `causa_raiz` | TEXT | — | Causa raiz identificada |
| `encaminhamento` | TEXT | — | Encaminhamento dado |
| `solucao_aplicada` | TEXT | — | Solução aplicada |
| `status_resolucao` | ENUM | — | aberto | andamento | resolvido |
| `data_resolucao` | DATETIME | — | Preenchida somente se resolvido (CHECK) |

## RESTAURACAO

| Atributo | Tipo | Chave | Descrição |
|---|---|---|---|
| `id_restauracao` | INT | PK | Identificador da restauração |
| `id_job` | INT | FK | Backup restaurado -> JOB_BACKUP |
| `id_usuario` | INT | FK | Quem solicitou -> USUARIO |
| `data_solicitacao` | DATETIME | — | Início da restauração |
| `data_conclusao` | DATETIME | — | Fim (>= data_solicitacao) |
| `motivo` | TEXT | — | Motivo da restauração |
| `rto_realizado_min` | INT | — | RTO efetivamente realizado (>= 0) |
| `resultado` | ENUM | — | sucesso | parcial | falha |

## LOG_AUDITORIA

| Atributo | Tipo | Chave | Descrição |
|---|---|---|---|
| `id_log` | INT | PK | Identificador do registro de auditoria |
| `id_usuario` | INT | FK | Autor da ação -> USUARIO (NULL se removido) |
| `tabela_afetada` | VARCHAR(50) | — | Tabela alterada |
| `acao` | ENUM | — | INSERT | UPDATE | DELETE |
| `id_registro` | INT | — | Chave do registro afetado |
| `data_hora` | DATETIME | — | Momento da ação |

## Relacionamentos

| Pai | Filho | Verbo | Cardinalidade | Ao excluir o pai |
|---|---|---|---|---|
| ATIVO_CRITICO | JOB_BACKUP | gera | 1:N | RESTRICT |
| JOB_BACKUP | FALHA | origina | 1:N | RESTRICT |
| JOB_BACKUP | RESTAURACAO | permite | 1:N | RESTRICT |
| USUARIO | FALHA | registra | 1:N | RESTRICT |
| USUARIO | RESTAURACAO | solicita | 1:N | RESTRICT |
| USUARIO | LOG_AUDITORIA | origina | 1:N | SET NULL |
