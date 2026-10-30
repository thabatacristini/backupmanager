-- =====================================================================
-- 04 — CONSULTAS (SELECT) usadas pelo painel de monitoramento e relatórios
-- =====================================================================
USE backupmanager;

-- C1: volume de registros por tabela
SELECT 'USUARIO' AS tabela, COUNT(*) AS registros FROM USUARIO
UNION ALL SELECT 'ATIVO_CRITICO', COUNT(*) FROM ATIVO_CRITICO
UNION ALL SELECT 'JOB_BACKUP',    COUNT(*) FROM JOB_BACKUP
UNION ALL SELECT 'FALHA',         COUNT(*) FROM FALHA
UNION ALL SELECT 'RESTAURACAO',   COUNT(*) FROM RESTAURACAO
UNION ALL SELECT 'LOG_AUDITORIA', COUNT(*) FROM LOG_AUDITORIA;

-- C2: taxa de sucesso por ativo (view com JOIN + GROUP BY)
SELECT * FROM vw_taxa_sucesso_por_ativo ORDER BY pct_sucesso;

-- C3: distribuição das falhas por categoria (GROUP BY + percentual)
SELECT categoria,
       COUNT(*) AS ocorrencias,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM FALHA), 1) AS pct_do_total
  FROM FALHA
 GROUP BY categoria
 ORDER BY ocorrencias DESC;

-- C4: falhas ainda não resolvidas, por ativo (JOIN de 4 tabelas via view)
SELECT nome_sistema,
       SUM(CASE WHEN status_resolucao = 'aberto'    THEN 1 ELSE 0 END) AS abertas,
       SUM(CASE WHEN status_resolucao = 'andamento' THEN 1 ELSE 0 END) AS em_andamento
  FROM vw_falhas_abertas
 GROUP BY nome_sistema
 ORDER BY abertas DESC;

-- C5: RTO realizado x meta, por ativo (JOIN + AVG + HAVING)
SELECT a.nome_sistema,
       a.rto_meta_min,
       COUNT(r.id_restauracao)            AS restauracoes,
       ROUND(AVG(r.rto_realizado_min), 1) AS rto_medio_min
  FROM RESTAURACAO r
  JOIN JOB_BACKUP j    ON j.id_job = r.id_job
  JOIN ATIVO_CRITICO a ON a.id_ativo = j.id_ativo
 GROUP BY a.nome_sistema, a.rto_meta_min
HAVING COUNT(r.id_restauracao) >= 1
 ORDER BY rto_medio_min DESC;

-- C6: ativos com taxa de falha acima da média geral (subconsulta)
SELECT nome_sistema, criticidade, total_jobs, jobs_falha,
       ROUND(100.0 * jobs_falha / total_jobs, 1) AS pct_falha
  FROM vw_taxa_sucesso_por_ativo
 WHERE 100.0 * jobs_falha / total_jobs >
       (SELECT 100.0 * SUM(CASE WHEN status = 'falha' THEN 1 ELSE 0 END) / COUNT(*) FROM JOB_BACKUP)
 ORDER BY pct_falha DESC;

-- C7: ações registradas por usuário na trilha de auditoria
SELECT u.nome, l.acao, COUNT(*) AS total
  FROM LOG_AUDITORIA l
  JOIN USUARIO u ON u.id_usuario = l.id_usuario
 GROUP BY u.nome, l.acao
 ORDER BY u.nome, l.acao;
