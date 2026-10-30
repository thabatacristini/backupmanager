# BackupManager

Sistema web de gestão de backup e recuperação de dados, desenvolvido como **ação de extensão**
do *Programa de Extensão UFMS Digital (95DX7.200525)*. O objetivo é oferecer a organizações
sem política de backup estruturada (instituições públicas, terceiro setor e pequenas empresas)
um modelo acessível, de baixo custo e alinhado à **LGPD** para registrar jobs de backup,
acompanhar falhas e medir o tempo de recuperação (RTO).

- **Autora:** Thabata Cristini de Oliveira Nascimento
- **Curso:** Tecnologia da Informação — Projeto Integrador de TI II
- **Módulo 3:** Banco de Dados e Controle de Versão (este repositório)

## O que há neste repositório

```
backupmanager/
├── database/
│   ├── schema.sql                 # DDL: 6 tabelas, restrições, índices e 2 views (MySQL 8)
│   ├── seed.sql                   # dados SINTÉTICOS (gerado por scripts/gerar_seed.py)
│   └── queries/
│       ├── 01_insercao.sql        # INSERT
│       ├── 02_atualizacao.sql     # UPDATE
│       ├── 03_remocao.sql         # DELETE
│       ├── 04_consultas.sql       # SELECT (JOIN, GROUP BY, HAVING, subconsulta)
│       └── 05_teste_restricoes.sql# 6 comandos que DEVEM falhar (FK, UNIQUE, CHECK)
├── docs/
│   ├── DER_backupmanager.png      # diagrama entidade-relacionamento
│   ├── DER_backupmanager.dot      # fonte do diagrama (Graphviz)
│   └── DICIONARIO_DE_DADOS.md     # dicionário de dados
├── scripts/
│   ├── gerar_seed.py              # gera database/seed.sql (semente fixa)
│   ├── gerar_der.py               # gera o DER e o dicionário de dados
│   └── validar_sqlite.py          # smoke test dos scripts SQL sem servidor MySQL
├── .env.example
└── .gitignore
```

> O código da aplicação web (Express + EJS + Tailwind CSS, Módulo 2) usa este banco e é mantido
> nas pastas `controllers/`, `models/`, `views/` e `routes/` na raiz do repositório.

## Como criar o banco (MySQL 8.0+)

```bash
mysql -u root -p < database/schema.sql      # cria o banco `backupmanager` e as tabelas
mysql -u root -p < database/seed.sql        # carrega dados sintéticos (847 jobs, 48 falhas)

# operações de manipulação, em ordem:
mysql -u root -p < database/queries/01_insercao.sql
mysql -u root -p < database/queries/02_atualizacao.sql
mysql -u root -p < database/queries/03_remocao.sql
mysql -u root -p < database/queries/04_consultas.sql
```

`05_teste_restricoes.sql` deve ser executado **comando a comando** (cada um precisa gerar erro).

**Senhas:** o `seed.sql` usa um marcador em `senha_hash`. Antes de usar o login da aplicação,
gere hashes reais (bcrypt) e atualize a tabela `USUARIO`.

## Modelo de dados

Seis entidades em 3ª Forma Normal: `USUARIO`, `ATIVO_CRITICO`, `JOB_BACKUP`, `FALHA`,
`RESTAURACAO` e `LOG_AUDITORIA`. Veja `docs/DER_backupmanager.png` e `docs/DICIONARIO_DE_DADOS.md`.

Principais regras de integridade:

| Regra | Onde |
|---|---|
| Não é possível apagar um ativo que tenha jobs | FK `ON DELETE RESTRICT` |
| Nome de ativo e e-mail de usuário são únicos | `UNIQUE` |
| Tamanho/duração/RTO não podem ser negativos | `CHECK` |
| Falha só tem `data_resolucao` se estiver `resolvido` | `CHECK chk_falha_resolucao` |
| Restauração não termina antes de começar | `CHECK chk_rest_datas` |
| Trilha de auditoria preservada se o usuário for removido | FK `ON DELETE SET NULL` |

## Dados de teste

Todos os dados são **sintéticos**. Reproduzem apenas o perfil estatístico dos logs analisados
na ação de extensão. Nenhum dado real de empresa ou de cidadão é versionado aqui.

## Fluxo de versionamento (Git)

- `main`: versão estável, somente via merge de `develop` + tag de versão (`vX.Y.Z`).
- `develop`: integração das funcionalidades.
- `feature/<nome>`: uma branch por funcionalidade, integrada com `merge --no-ff`.
- Mensagens de commit no padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/):
  `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`.

## Validação sem MySQL

```bash
python3 scripts/validar_sqlite.py
```

Traduz o dialeto MySQL para SQLite, executa tudo e confere que as 6 violações de
`05_teste_restricoes.sql` são bloqueadas. É um teste rápido de lógica; a validação oficial
é no MySQL 8.

## Licença

MIT — uso livre por organizações públicas e do terceiro setor.
