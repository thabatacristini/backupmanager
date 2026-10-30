-- =====================================================================
-- 03 — REMOÇÃO (DELETE)
-- Ordem obrigatória: filhos antes dos pais (FKs com ON DELETE RESTRICT).
-- A trilha de auditoria (LOG_AUDITORIA) nunca é apagada.
-- =====================================================================
USE backupmanager;

DELETE FROM FALHA          WHERE id_falha = 49;
DELETE FROM JOB_BACKUP     WHERE id_job = 848;
DELETE FROM ATIVO_CRITICO  WHERE nome_sistema = 'SRV-TESTE-99';

INSERT INTO LOG_AUDITORIA (id_usuario, tabela_afetada, acao, id_registro, data_hora)
VALUES (1, 'ATIVO_CRITICO', 'DELETE', 6, '2026-04-29 10:30:00');
