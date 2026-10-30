-- =====================================================================
-- 01 — INSERÇÃO (INSERT)
-- Executar após schema.sql e seed.sql:  mysql -u root -p backupmanager < 01_insercao.sql
-- =====================================================================
USE backupmanager;

-- 1.1 Cadastrar um novo ativo crítico (ativo temporário de teste)
INSERT INTO ATIVO_CRITICO (nome_sistema, tipo, criticidade, responsavel, descricao, rto_meta_min, rpo_meta_min)
VALUES ('SRV-TESTE-99', 'Servidor de Aplicação', 'baixa', 'Equipe de Infraestrutura',
        'Ativo temporário para validar inserção e remoção', 1440, 4320);

-- 1.2 Registrar um job de backup para o novo ativo (o id do ativo é obtido por subconsulta)
INSERT INTO JOB_BACKUP (id_ativo, data_execucao, tipo_backup, status, tamanho_gb, duracao_min, destino)
VALUES ((SELECT id_ativo FROM ATIVO_CRITICO WHERE nome_sistema = 'SRV-TESTE-99'),
        '2026-04-29 01:00:00', 'completo', 'falha', 0, 4, 'DISCO-LOCAL');

-- 1.3 Registrar a falha ocorrida nesse job (job 848 = primeiro id após os 847 do seed)
INSERT INTO FALHA (id_job, id_usuario, data_registro, categoria, descricao_erro, status_resolucao)
VALUES (848, 2, '2026-04-29 02:00:00', 'timeout_rede',
        'Job interrompido por timeout de rede (ERR_TIMEOUT).', 'aberto');

-- 1.4 Registrar a ação na trilha de auditoria (falha 49 = primeiro id após as 48 do seed)
INSERT INTO LOG_AUDITORIA (id_usuario, tabela_afetada, acao, id_registro, data_hora)
VALUES (2, 'FALHA', 'INSERT', 49, '2026-04-29 02:00:00');
