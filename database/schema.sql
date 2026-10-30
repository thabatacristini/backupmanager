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

