-- =====================================================================
-- BackupManager — Esquema do banco de dados (MySQL 8.0+)
-- Execução: mysql -u root -p < database/schema.sql
-- =====================================================================
CREATE DATABASE IF NOT EXISTS backupmanager
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE backupmanager;

DROP VIEW  IF EXISTS vw_falhas_abertas;
DROP VIEW  IF EXISTS vw_taxa_sucesso_por_ativo;
DROP TABLE IF EXISTS LOG_AUDITORIA;
DROP TABLE IF EXISTS RESTAURACAO;
DROP TABLE IF EXISTS FALHA;
DROP TABLE IF EXISTS JOB_BACKUP;
DROP TABLE IF EXISTS ATIVO_CRITICO;
DROP TABLE IF EXISTS USUARIO;

-- ---------------------------------------------------------------------
-- USUARIO: controle de acesso e rastreabilidade (LGPD, art. 46)
-- ---------------------------------------------------------------------
CREATE TABLE USUARIO (
  id_usuario       INT AUTO_INCREMENT PRIMARY KEY,
  nome             VARCHAR(100) NOT NULL,
  cargo            VARCHAR(80),
  email            VARCHAR(120) NOT NULL,
  senha_hash       VARCHAR(255) NOT NULL,           -- hash bcrypt, nunca texto puro
  perfil_acesso    ENUM('admin','analista') NOT NULL DEFAULT 'analista',
  tentativas_login INT NOT NULL DEFAULT 0,
  bloqueado_ate    DATETIME NULL,
  criado_em        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_usuario_email UNIQUE (email),
  CONSTRAINT chk_usuario_tentativas CHECK (tentativas_login >= 0)
);

-- ---------------------------------------------------------------------
-- ATIVO_CRITICO: inventário de sistemas protegidos (+ metas de RTO/RPO)
-- ---------------------------------------------------------------------
CREATE TABLE ATIVO_CRITICO (
  id_ativo      INT AUTO_INCREMENT PRIMARY KEY,
  nome_sistema  VARCHAR(100) NOT NULL,
  tipo          VARCHAR(50)  NOT NULL,
  criticidade   ENUM('alta','media','baixa') NOT NULL,
  responsavel   VARCHAR(100) NOT NULL,
  descricao     TEXT,
  rto_meta_min  INT NOT NULL,                       -- meta de tempo de recuperação
  rpo_meta_min  INT NOT NULL,                       -- meta de perda de dados tolerável
  criado_em     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_ativo_nome UNIQUE (nome_sistema),
  CONSTRAINT chk_ativo_rto CHECK (rto_meta_min > 0),
  CONSTRAINT chk_ativo_rpo CHECK (rpo_meta_min > 0)
);

-- ---------------------------------------------------------------------
-- JOB_BACKUP: cada execução de backup de um ativo
-- ---------------------------------------------------------------------
CREATE TABLE JOB_BACKUP (
  id_job         INT AUTO_INCREMENT PRIMARY KEY,
  id_ativo       INT NOT NULL,
  data_execucao  DATETIME NOT NULL,
  tipo_backup    ENUM('completo','incremental','diferencial') NOT NULL,
  status         ENUM('ok','falha','andamento') NOT NULL DEFAULT 'andamento',
  tamanho_gb     DECIMAL(10,2) NOT NULL DEFAULT 0,
  duracao_min    INT NOT NULL DEFAULT 0,
  destino        VARCHAR(100) NOT NULL,
  CONSTRAINT fk_job_ativo FOREIGN KEY (id_ativo)
    REFERENCES ATIVO_CRITICO (id_ativo) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_job_tamanho CHECK (tamanho_gb >= 0),
  CONSTRAINT chk_job_duracao CHECK (duracao_min >= 0)
);

-- ---------------------------------------------------------------------
-- FALHA: registro estruturado de erros (causa, encaminhamento, solução)
-- ---------------------------------------------------------------------
CREATE TABLE FALHA (
  id_falha          INT AUTO_INCREMENT PRIMARY KEY,
  id_job            INT NOT NULL,
  id_usuario        INT NOT NULL,
  data_registro     DATETIME NOT NULL,
  categoria         ENUM('timeout_rede','espaco_insuficiente','credencial_expirada','outro') NOT NULL,
  descricao_erro    TEXT NOT NULL,
  causa_raiz        TEXT,
  encaminhamento    TEXT,
  solucao_aplicada  TEXT,
  status_resolucao  ENUM('aberto','andamento','resolvido') NOT NULL DEFAULT 'aberto',
  data_resolucao    DATETIME NULL,
  CONSTRAINT fk_falha_job FOREIGN KEY (id_job)
    REFERENCES JOB_BACKUP (id_job) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_falha_usuario FOREIGN KEY (id_usuario)
    REFERENCES USUARIO (id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE,
  -- falha só pode ter data de resolução se estiver resolvida (e vice-versa)
  CONSTRAINT chk_falha_resolucao CHECK (
    (status_resolucao = 'resolvido' AND data_resolucao IS NOT NULL) OR
    (status_resolucao <> 'resolvido' AND data_resolucao IS NULL)
  )
);

-- ---------------------------------------------------------------------
-- RESTAURACAO: processos de recuperação e RTO efetivamente realizado
-- ---------------------------------------------------------------------
CREATE TABLE RESTAURACAO (
  id_restauracao     INT AUTO_INCREMENT PRIMARY KEY,
  id_job             INT NOT NULL,
  id_usuario         INT NOT NULL,
  data_solicitacao   DATETIME NOT NULL,
  data_conclusao     DATETIME NULL,
  motivo             TEXT NOT NULL,
  rto_realizado_min  INT NOT NULL,
  resultado          ENUM('sucesso','parcial','falha') NOT NULL,
  CONSTRAINT fk_rest_job FOREIGN KEY (id_job)
    REFERENCES JOB_BACKUP (id_job) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_rest_usuario FOREIGN KEY (id_usuario)
    REFERENCES USUARIO (id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_rest_rto CHECK (rto_realizado_min >= 0),
  CONSTRAINT chk_rest_datas CHECK (data_conclusao IS NULL OR data_conclusao >= data_solicitacao)
);

-- ---------------------------------------------------------------------
-- LOG_AUDITORIA: quem fez o quê e quando (defeito D06 da inspeção / RF08)
-- ---------------------------------------------------------------------
CREATE TABLE LOG_AUDITORIA (
  id_log          INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario      INT NULL,
  tabela_afetada  VARCHAR(50) NOT NULL,
  acao            ENUM('INSERT','UPDATE','DELETE') NOT NULL,
  id_registro     INT NULL,
  data_hora       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_log_usuario FOREIGN KEY (id_usuario)
    REFERENCES USUARIO (id_usuario) ON DELETE SET NULL ON UPDATE CASCADE
);

