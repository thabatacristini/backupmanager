-- =====================================================================
-- 02 — ATUALIZAÇÃO (UPDATE)
-- =====================================================================
USE backupmanager;

-- 2.1 Resolver a falha 49: status e data_resolucao precisam mudar juntos (CHECK chk_falha_resolucao)
UPDATE FALHA
   SET status_resolucao = 'resolvido',
       causa_raiz       = 'Instabilidade momentânea no enlace de rede',
       solucao_aplicada = 'Janela reagendada e timeout do agente ajustado',
       data_resolucao   = '2026-04-29 09:30:00'
 WHERE id_falha = 49;

-- 2.2 Atualizar um atributo de um ativo
UPDATE ATIVO_CRITICO
   SET responsavel = 'Equipe de Segurança da Informação'
 WHERE nome_sistema = 'SRV-MAIL-01';

-- 2.3 Atualização em lote: preencher o encaminhamento das falhas de rede que ainda não o possuem
UPDATE FALHA
   SET encaminhamento = 'Equipe de redes acionada para análise do enlace'
 WHERE categoria = 'timeout_rede'
   AND encaminhamento IS NULL;

-- 2.4 Registrar as ações na trilha de auditoria
INSERT INTO LOG_AUDITORIA (id_usuario, tabela_afetada, acao, id_registro, data_hora)
VALUES (2, 'FALHA', 'UPDATE', 49, '2026-04-29 09:30:00'),
       (1, 'ATIVO_CRITICO', 'UPDATE', 5, '2026-04-29 10:00:00');
