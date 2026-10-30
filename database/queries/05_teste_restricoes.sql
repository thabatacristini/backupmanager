-- =====================================================================
-- 05 — TESTE DE RESTRIÇÕES: cada comando abaixo DEVE FALHAR.
-- Execute um por vez (o primeiro erro interrompe um script inteiro).
-- Códigos esperados no MySQL 8: 1451, 1452, 1062, 3819.
-- =====================================================================
USE backupmanager;

-- R1: excluir ativo que possui jobs                -> FK RESTRICT (erro 1451)
DELETE FROM ATIVO_CRITICO WHERE nome_sistema = 'SRV-DB-01';

-- R2: job para ativo inexistente                   -> FK (erro 1452)
INSERT INTO JOB_BACKUP (id_ativo, data_execucao, tipo_backup, status, tamanho_gb, duracao_min, destino)
VALUES (999, '2026-04-29 01:00:00', 'completo', 'ok', 10, 5, 'DISCO-LOCAL');

-- R3: ativo com nome duplicado                     -> UNIQUE (erro 1062)
INSERT INTO ATIVO_CRITICO (nome_sistema, tipo, criticidade, responsavel, rto_meta_min, rpo_meta_min)
VALUES ('SRV-DB-01', 'Servidor de Banco de Dados', 'alta', 'Equipe de Banco de Dados', 240, 240);

-- R4: job com tamanho negativo                     -> CHECK (erro 3819)
INSERT INTO JOB_BACKUP (id_ativo, data_execucao, tipo_backup, status, tamanho_gb, duracao_min, destino)
VALUES (1, '2026-04-29 01:00:00', 'completo', 'ok', -5, 5, 'DISCO-LOCAL');

-- R5: resolver falha sem informar data_resolucao   -> CHECK (erro 3819)
UPDATE FALHA SET status_resolucao = 'resolvido' WHERE id_falha = 48;

-- R6: restauração concluída antes de solicitada    -> CHECK (erro 3819)
INSERT INTO RESTAURACAO (id_job, id_usuario, data_solicitacao, data_conclusao, motivo, rto_realizado_min, resultado)
VALUES (1, 2, '2026-04-29 10:00:00', '2026-04-29 09:00:00', 'Teste', 10, 'sucesso');
