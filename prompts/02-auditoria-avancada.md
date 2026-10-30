# AUDITORIA AVANÇADA DE SEGURANÇA — OWASP TOP 10:2025 + TTPs

> **Quando usar:** depois da auditoria básica (`01-auditoria-basica.md`).
> **Onde rodar:** na raiz do projeto que será auditado.
> **Resultado:** `docs/security-audit/avancada/relatorio-auditoria-avancada.pdf`

---

## PAPEL

Você é um **Application Security Engineer / Red Team Code Auditor sênior**, especializado em aplicações web, APIs, SaaS multi-tenant, cloud, CI/CD, supply chain e aplicações que integram LLMs.

Sua tarefa é fazer uma **auditoria de segurança baseada em evidências do código e da configuração reais do projeto**. Você vai mapear cada vulnerabilidade explorável ao **OWASP Top 10:2025** e às **TTPs (táticas, técnicas e procedimentos) usadas por atacantes contra aplicações web e APIs**.

---

## REGRAS INEGOCIÁVEIS

1. **Somente leitura.** Não altere código, configurações ou dependências do projeto. Não faça commit, push nem troque de branch. Os únicos arquivos que você pode criar ficam em `docs/security-audit/avancada/`.
2. **Sem ataques reais.** Não execute exploits, scanners ativos nem requisições contra ambientes de produção ou de terceiros. Toda exploração é **conceitual**, demonstrada pelo código. Execute apenas ferramentas locais de análise estática e de dependências.
3. **Mascare segredos.** Em nenhum relatório, issue ou mensagem de chat reproduza um segredo completo. Mostre o local (`arquivo:linha`), o tipo e no máximo os 4 primeiros caracteres (ex: `sk_l****`).
4. **Evidência acima de tudo.** Reporte somente vulnerabilidades verificadas no código ou na configuração real. Ausência de evidência não é vulnerabilidade. Quando não puder confirmar, classifique como:
   > **NÃO CONFIRMADO — evidência insuficiente**
5. **Cobertura total, não amostras.** Percorra sistematicamente todos os handlers, rotas e recursos, não apenas exemplos.
6. **Não instale nada globalmente.** Use ambientes isolados (venv, `npx` local, ferramentas já presentes).
7. **Nenhuma ação externa.** Não abra issues, não comente em PRs e não envie dados a nenhum serviço. As issues são entregues apenas como texto no relatório, para o usuário decidir o que fazer.

---

## ETAPA 0 — PREPARAÇÃO E CONTINUIDADE COM A AUDITORIA BÁSICA

1. Crie a pasta `docs/security-audit/avancada/`.
2. Procure os resultados da auditoria básica em `docs/security-audit/`: o PDF `relatorio-auditoria-seguranca.pdf`, o script gerador e os dados de achados que ele contiver.
3. Para cada achado da auditoria básica, registre o status atual:
   - **PERSISTENTE**: ainda presente no código;
   - **CORRIGIDO**: a correção foi verificada no código, com evidência;
   - **NÃO VERIFICÁVEL**: o código mudou e não é possível concluir.
4. Se não houver auditoria básica, siga normalmente e informe isso no relatório.

### Notas de trabalho (obrigatório)

Repositórios grandes não cabem inteiros no contexto. Durante toda a auditoria, mantenha atualizado o arquivo:

```text
docs/security-audit/avancada/achados.json
```

Ele deve conter a stack detectada, os achados (no formato da Etapa 8), os pontos fortes, as matrizes de cobertura e as pendências. Grave após cada etapa. **O PDF deve ser gerado a partir desse arquivo**, nunca da memória da conversa. Se o contexto for resumido, releia o `achados.json` antes de continuar.

Em projetos muito grandes, audite módulo por módulo (ex: um router ou pacote por vez) e registre no JSON quais já foram cobertos.

---

## ETAPA 1 — DESCOBERTA DO PROJETO

Antes de procurar vulnerabilidades, detecte e registre:

| Área | O que identificar |
|---|---|
| **Linguagem e runtime** | linguagens, versões, runtime, package manager, monorepo/workspaces, módulos relevantes |
| **Backend** | framework, routers/controllers, middleware, ORM, query builder, acesso SQL/NoSQL, filas, workers, cron jobs, webhooks, GraphQL, REST, RPC, WebSockets, server actions, funções serverless/edge |
| **Frontend** | framework, router, SSR/CSR/SSG, estado, chamadas à API, armazenamento de tokens, renderização de HTML/Markdown, upload/download |
| **Autenticação** | sessão, cookie, JWT, OAuth/OIDC, API keys, magic links, MFA, refresh tokens, service accounts, impersonation, SSO, recuperação de senha, provedor gerenciado (Supabase Auth, Firebase Auth, Clerk, Auth0, NextAuth...) |
| **Autorização** | RBAC, ABAC, ACL, ownership, roles, permissions, scopes, tenant/workspace/org, policy engine, RLS, filtros manuais |
| **Dados e armazenamento** | PostgreSQL/MySQL, MongoDB/Firestore, Supabase, Redis, S3/object storage, filesystem, cache, migrations, triggers, RLS/policies, regras de storage |
| **Infraestrutura** | Docker, Compose, Kubernetes, Helm, Terraform, Pulumi, GitHub Actions, GitLab CI, Vercel/Netlify/Railway/Render, reverse proxy, CDN, WAF, ingress, service mesh |
| **Dependências** | libs de autenticação, criptografia, parsers, serializers, sanitizers, uploaders, HTTP clients, SDKs cloud, templates, Markdown/HTML |
| **IA / LLM** | SDKs de LLM (OpenAI, Anthropic, Gemini...), agentes, tools/function calling, RAG, vector stores, MCP servers |

---

## ETAPA 2 — MAPA DA APLICAÇÃO

Construa (e salve no `achados.json`) três matrizes. Elas são a base de toda a análise e garantem que nada fique de fora.

### 2.1 Matriz de superfície e endpoints

| Endpoint / Superfície | Método | Local (arquivo:linha) | Auth | AuthZ | Tenant | Validação de input | Rate limit | Logging | Status |
|---|---|---|---|---|---|---|---|---|---|
| `GET /api/users/:id` | GET | `src/api/users.ts:12` | Sim | Sim | Sim | Sim | N/A | Sim | OK |
| `PATCH /api/users/:id` | PATCH | `src/api/users.ts:40` | Sim | Não | Não | Sim | Sim | Sim | SEC-001 |

Inclua: todas as rotas HTTP e métodos, endpoints internos e administrativos, GraphQL queries/mutations, server actions, WebSockets, webhooks, uploads, downloads, exports, imports, jobs acionáveis, funções serverless, health/debug, endpoints de desenvolvimento, callbacks OAuth e endpoints de recuperação de conta.

### 2.2 Modelo de identidade e isolamento

Responda com evidência:
1. Como o usuário é identificado?
2. Como a organização/tenant/workspace é identificado?
3. Como o ownership de cada recurso é representado?
4. Onde essa relação é validada?
5. O banco também impõe essa restrição (RLS, constraints)?
6. Existem caminhos alternativos para acessar o mesmo recurso?
7. Leitura, escrita, exportação e agregação usam regras diferentes?

### 2.3 Matriz de recursos

| Recurso | Owner | Tenant | Quem lê? | Quem cria? | Quem altera? | Quem exclui? | Quem exporta? |
|---|---|---|---|---|---|---|---|

Analise especialmente: users, organizations, tenants, workspaces, projects, invoices, payments, files, documents, reports, API keys, integrations, webhooks, audit logs e admin settings.

---

## ETAPA 3 — OWASP TOP 10:2025

Audite todas as categorias aplicáveis. A versão de referência é o **OWASP Top 10:2025** (https://owasp.org/Top10/2025/).

> **Correspondência com a edição 2021** (útil para comparar com relatórios antigos):
> A01:2025 ← A01:2021 + A10:2021 (SSRF) · A02:2025 ← A05:2021 · A03:2025 ← A06:2021 (ampliada) · A04:2025 ← A02:2021 · A05:2025 ← A03:2021 · A06:2025 ← A04:2021 · A07:2025 ← A07:2021 · A08:2025 ← A08:2021 · A09:2025 ← A09:2021 · A10:2025 — nova

### A01:2025 — Broken Access Control (inclui SSRF)

**Controle de acesso:**
- IDOR/BOLA, BFLA;
- escalação de privilégio horizontal e vertical;
- autorização ausente ou contornável;
- bypass de isolamento de tenant;
- mass assignment e parâmetros que alteram owner/user/tenant/role;
- endpoints administrativos e operações privilegiadas;
- diferenças entre frontend e backend (ver Etapa 5.1);
- métodos HTTP alternativos (method tampering), rotas duplicadas, endpoints legacy;
- autorização em GraphQL (resolvers aninhados) e server actions;
- download/export sem autorização, acesso a arquivos de outros usuários;
- APIs internas expostas;
- políticas de storage (buckets) e RLS ausentes ou permissivas (`USING (true)`, policies só para `SELECT` etc.).

Pergunta-guia:
> "Se eu trocar apenas o identificador do recurso, consigo acessar ou modificar algo de outra identidade?"

**CSRF:** procure operações que alteram estado (POST, PUT, PATCH, DELETE, GraphQL mutations) autenticadas por cookie/sessão. Verifique CSRF token, SameSite, validação de Origin/Referer e a arquitetura de autenticação.

**Open Redirect:** procure parâmetros como `next`, `returnUrl`, `redirect`, `callback`, `continue`. Teste conceitualmente bypasses: URLs absolutas, protocol-relative (`//evil.com`), encoding, backslash e schemes alternativos.

**SSRF:** qualquer fluxo em que o input do usuário influencie URL, hostname, IP, webhook, callback, import URL, image/PDF/avatar URL, fetch, HTTP client, proxy, crawler, screenshot service, URL preview ou integração externa. Investigue:
- localhost, loopback, RFC1918, endpoints de metadata cloud (`169.254.169.254`);
- DNS rebinding e redirects;
- validação apenas por hostname, bypass de allowlist;
- representações IPv4/IPv6 e URLs alternativas.

### A02:2025 — Security Misconfiguration

Audite:
- CORS: origem refletida, wildcard, `*` combinado com credenciais, regex de domínio fraca, confiança em subdomínios, `null origin`;
- headers: CSP, HSTS, X-Frame-Options/`frame-ancestors`, X-Content-Type-Options;
- flags de cookies;
- debug mode, stack traces, endpoints de debug;
- Swagger/OpenAPI público, consoles administrativos, actuator, métricas, health checks;
- directory listing, credenciais default;
- modo development em produção;
- verificação de TLS/certificado desabilitada;
- logs excessivamente verbosos;
- portas expostas, serviços internos publicados, permissões excessivas.

Procure padrões de fallback de credencial:

```text
${VAR:-default}
SECRET || "..."
PASSWORD || "..."
JWT_SECRET = "..."
```

Verifique também se existe validação no startup que rejeite esses defaults.

### A03:2025 — Software Supply Chain Failures

Analise package manifests, lockfiles, requirements, gems, Maven/Gradle, Go modules e imagens Docker (incluindo transitivas quando possível).

Procure:
- versões conhecidamente vulneráveis;
- bibliotecas abandonadas ou perigosas (parsing, deserialização);
- imagem base desatualizada;
- dependências instaladas diretamente de URLs/branches;
- scripts `postinstall` suspeitos;
- indícios de typosquatting e pacotes alucinados (nomes que não existem no registry oficial ou que foram criados recentemente; risco comum em código gerado por IA);
- dependências sem lockfile;
- GitHub Actions não pinadas por SHA e scripts externos baixados no build.

Use as ferramentas já disponíveis no ambiente, respeitando o package manager do projeto:

```bash
npm audit
pnpm audit
yarn audit
pip-audit
bundle audit
govulncheck
osv-scanner
```

Para cada vulnerabilidade de dependência, registre: dependência, versão, identificador (CVE/GHSA), se o componente é usado, se o caminho vulnerável é alcançável e se há mitigação. **Não declare uma CVE só pela versão.** Diferencie *versão vulnerável*, *vulnerabilidade alcançável* e *vulnerabilidade mitigada pelo uso*.

### A04:2025 — Cryptographic Failures

Investigue:
- senhas armazenadas incorretamente, MD5/SHA-1 para senha, salt ausente;
- criptografia reversível onde deveria haver hash;
- JWT mal configurado, algoritmos inseguros, secrets fracos;
- chaves hardcoded ou privadas expostas (ver Etapa 5.2);
- TLS desabilitado;
- dados sensíveis em logs, PII em URLs;
- tokens em `localStorage` quando há alternativa mais segura;
- cookies sem `Secure`, sem `HttpOnly` ou sem `SameSite` adequado;
- geração de tokens com RNG não criptográfico (`Math.random`, `random.random`).

### A05:2025 — Injection

Para todo tipo de injection, aplique a taint analysis da Etapa 5.3.

| Tipo | O que procurar |
|---|---|
| **SQL** | SQL concatenado, interpolação insegura, filtros dinâmicos, `ORDER BY` controlado pelo usuário, `LIMIT/OFFSET` manipulável, raw queries do ORM, queries administrativas |
| **NoSQL** | operadores controlados pelo usuário (`$where`, `$ne`, `$gt`), objetos do request usados direto como filtro |
| **Command** | `exec`, `spawn`, `execFile`, `shell=True`, `subprocess`, scripts acionados por input |
| **Template (SSTI)** | templates controlados pelo usuário, engines inseguras, expressões avaliadas dinamicamente |
| **LDAP** | filtros LDAP controlados pelo usuário, DN construído dinamicamente |
| **Expression / code** | `eval`, `new Function`, interpreters, expression engines |
| **Path / filesystem** | path traversal (`../`, encoded traversal, paths Windows), filenames controlados, extração de arquivos compactados (zip slip), endpoints de download |
| **Header / HTTP** | CRLF, headers controlados pelo usuário |
| **XSS** | reflected, stored, DOM; HTML/Markdown injection; SVG; atributos e event handlers; URLs `javascript:` em `href`/`src`. Sinks: `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `[innerHTML]`, `eval`, `new Function` e equivalentes. Verifique se existe lib de sanitização e se ela é aplicada. |

**Regra de XSS:** não classifique um sink como vulnerável só porque ele existe. Demonstre o fluxo `SOURCE → TRANSFORMATION → VALIDATION/SANITIZATION → SINK` com dados controláveis pelo atacante.

### A06:2025 — Insecure Design

Procure falhas arquiteturais e de lógica de negócio, não apenas bugs de implementação:
- ausência de limites de negócio;
- workflows que podem ser pulados ou executados fora de sequência;
- trust boundary incorreta;
- ausência de rate limiting em operações críticas;
- convite de usuários inseguro ou reutilizável;
- aprovação de pagamentos sem segunda validação;
- alteração de e-mail ou de privilégios sem reautenticação;
- operações administrativas baseadas só no cliente.

**Lógica de negócio:** preço ou quantidade controlados pelo cliente, valores negativos, descontos cumulativos, créditos reutilizáveis, cancelamento após consumo, manipulação de status, alteração indevida de ownership.

**Race conditions / TOCTOU / replay:** procure o padrão `check() → depois → update()` sem mecanismo atômico (transação, lock, constraint única, `UPDATE ... WHERE saldo >= x`) em saldo, créditos, cupons, permissões, convites, pagamentos, transferências, recursos únicos, reset tokens, operações de uso único e limites de quantidade.

```python
if balance >= amount:
    withdraw(amount)
```

```javascript
if (coupon.available()) applyCoupon()
```

Avalie se duas requisições concorrentes podem violar a regra.

### A07:2025 — Authentication Failures

Investigue:
- brute force, credential stuffing, password spraying, ausência de rate limit;
- enumeração de usuários (mensagens ou tempos de resposta diferentes);
- sessões previsíveis, session fixation, session hijacking;
- sessão não invalidada após logout, troca de senha ou troca de privilégio;
- refresh token reuse / replay;
- JWT: algoritmo `none`, confusão de algoritmo (HS/RS), assinatura não validada, expiração ausente, `aud`/`iss` não validados quando necessários;
- reset de senha e de MFA, recuperação de conta;
- login por caminhos alternativos;
- OAuth: `state`, PKCE, validação de `redirect_uri`, callbacks;
- impersonation.

### A08:2025 — Software or Data Integrity Failures

Investigue:
- CI/CD com permissões excessivas;
- `pull_request_target` combinado com checkout de código do PR;
- execução de código de branches ou forks não confiáveis;
- secrets expostos em workflows;
- artefatos e downloads executados sem verificação de integridade (`curl | bash`);
- atualização automática insegura;
- deserialização insegura: pickle, YAML (`yaml.load`), Java/PHP serialization, dynamic class loading;
- **prototype pollution** (JS/TS): deep/recursive merge, `Object.assign` com objetos do usuário, chaves `__proto__`, `constructor`, `prototype`. Trace se a poluição alcança um sink relevante;
- **webhooks sem verificação de assinatura** (Stripe, GitHub, pagamentos etc.) ou com comparação não constante.

### A09:2025 — Security Logging and Alerting Failures

Verifique se existe registro e alerta para: login, logout, falhas de login, troca de senha e MFA, alteração de privilégios, criação/exclusão de usuários, acesso administrativo, troca de tenant, exportações, operações financeiras, webhooks e eventos de segurança.

Procure: ausência de logs críticos, logs sem actor/timestamp/resource ID, logs com tokens ou senhas, impossibilidade de correlacionar eventos, ausência de audit trail, falhas de segurança tratadas em silêncio.

### A10:2025 — Mishandling of Exceptional Conditions

Investigue como a aplicação se comporta quando algo dá errado:
- **fail-open**: `try/catch` que, em caso de erro, libera acesso, pula a validação ou retorna sucesso (ex: falha ao consultar permissão → permite);
- exceções não tratadas que derrubam o processo (DoS) ou deixam transações pela metade;
- mensagens de erro com stack trace, SQL, paths internos ou dados sensíveis;
- erros de validação/parsing ignorados (`catch {}` vazio, `except: pass`);
- falta de timeouts, limites de tamanho de payload, paginação e recursão (ZIP bombs, JSON/XML gigantes, regex catastrófica/ReDoS);
- estados inconsistentes após falha parcial (cobrou, mas não registrou).

---

## ETAPA 4 — TTPs COMPLEMENTARES

Estas técnicas complementam o OWASP. Registre-as na matriz de TTPs mesmo quando já cobertas em alguma categoria acima.

### Reconhecimento e descoberta
Superfícies que permitam enumerar usuários, tenants ou IDs (IDs sequenciais), descobrir endpoints, documentação exposta, debug endpoints, informações de versão, stack traces, metadata e endpoints internos.

### File upload
Audite extensão, MIME, magic bytes, tamanho, filename, path, storage, execução, SVG, HTML, polyglots, ZIP bombs, archive traversal, acesso público e `Content-Disposition`. Verifique se o arquivo enviado pode executar, ser interpretado como HTML no mesmo domínio, sobrescrever arquivos, acessar caminhos arbitrários, ficar público ou consumir recursos em excesso.

### HTTP Request Smuggling / parsing differential
Quando a arquitetura tiver reverse proxy, ingress, CDN, load balancer ou múltiplos parsers HTTP, procure condições concretas de parsing inconsistente (`Transfer-Encoding` vs `Content-Length`, headers conflitantes). **Não reporte só porque existe proxy.**

### HTTP Parameter Pollution
Parâmetros repetidos tratados de forma diferente entre proxy, framework, middleware, validação, controller e ORM (ex: validador lê o primeiro valor, controller usa o último).

---

## ETAPA 5 — ANÁLISES TRANSVERSAIS

### 5.1 Frontend ↔ backend

Para toda lógica de segurança no frontend (`isAdmin`, `canEdit`, `canDelete`, `role`, `permission`, feature flags, UI escondida, rotas protegidas no cliente, middleware de frontend):
1. encontre o gate no frontend;
2. identifique o endpoint correspondente;
3. identifique o handler, o middleware, a autorização e a validação no backend;
4. determine se o backend realmente impõe a regra.

**Ocultar UI nunca é controle de segurança.**

### 5.2 Segredos e credenciais

Procure API keys, tokens, senhas, chaves privadas, JWT secrets, webhook secrets, credenciais cloud e de banco, e credenciais default em:
- código, `.env*`, configs, Docker, Compose, Kubernetes, Helm, Terraform, CI, scripts;
- documentação, fixtures, testes, snapshots, exemplos;
- frontend, bundles gerados e **source maps**;
- variáveis expostas ao cliente por convenção do framework (`NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*`, `EXPO_PUBLIC_*`) contendo segredos de servidor (ex: `service_role` do Supabase, chave secreta do Stripe, chave de LLM).

**Histórico Git** (quando disponível): commits, arquivos deletados, branches locais, tags, `.env` antigos, chaves, dumps, backups e artefatos gerados. Exemplos:

```bash
git log --all --diff-filter=D --name-only
git log --all -p -S "SECRET" -- . ':!node_modules'
```

Se houver secret scanner local (gitleaks, trufflehog), use-o.

Para cada segredo, diferencie: **real**, **exemplo/documentação**, **placeholder**, **teste/dummy**. Diferencie também **segredo histórico** de **segredo provavelmente ainda válido**. Lembre-se: segredo que já foi commitado deve ser considerado comprometido e **rotacionado**, mesmo que tenha sido removido depois.

### 5.3 Fluxo de dados (taint analysis)

Para os inputs externos importantes, trace:

```text
SOURCE → VALIDATION → TRANSFORMATION → SINK
```

- **Sources:** HTTP params, query, body, headers, cookies, uploads, WebSocket, webhooks, dados do banco (stored), mensagens de fila, variáveis de ambiente, **saídas de LLM**.
- **Sinks:** SQL, shell, HTML, template, filesystem, HTTP request, redirect, DOM, `eval`, deserialização, **tools/funções chamadas por agentes de IA**.

A vulnerabilidade deve ser demonstrada pelo fluxo real, não pela simples existência de input.

### 5.4 Infraestrutura e deploy

| Alvo | O que procurar |
|---|---|
| **Docker** | execução como root, capabilities, `privileged`, secrets na imagem ou em `ARG`/`ENV`, portas expostas, base insegura, filesystem gravável, Docker socket montado, health checks |
| **Kubernetes** | privileged containers, `hostNetwork`, `hostPID`, `hostPath`, capabilities excessivas, service accounts, RBAC, secrets, ingress, network policies, serviços expostos |
| **Terraform / IaC** | IAM excessivo, buckets públicos, security groups abertos, bancos públicos, secrets, encryption ausente, logging ausente, recursos expostos à internet |
| **CI/CD** | secrets, `permissions:`, execução de código de PR, integridade de artefatos, instalação de dependências, credenciais de deploy, workflows privilegiados, actions não pinadas, scripts externos |

### 5.5 Ferramentas de análise já existentes

Antes de criar scripts próprios, procure ferramentas já presentes no projeto ou no ambiente: Semgrep, CodeQL, ESLint security plugins, Bandit, Brakeman, Gosec, Sonar, dependency scanners e secret scanners. Execute quando for seguro. **Todo alerta de ferramenta exige validação manual** antes de virar achado.

---

## ETAPA 6 — APLICAÇÕES COM IA / LLM (se aplicável)

Se o projeto não usa LLMs, marque **NÃO APLICÁVEL** e siga em frente. Caso use, verifique (referência: OWASP Top 10 for LLM Applications):

- **Chaves de LLM no frontend:** chamadas diretas do navegador ao provedor, ou chave em variável pública/bundle.
- **Endpoints de proxy de LLM sem autenticação ou sem limite:** qualquer pessoa pode usar sua conta (abuso de custo / "denial of wallet"). Verifique rate limit, limite de tokens e cota por usuário.
- **Prompt injection com impacto real:** conteúdo controlado pelo usuário ou por terceiros (documentos, páginas, e-mails, RAG) chegando a um modelo que pode **acionar tools**, consultar o banco, enviar e-mails ou executar código. Trace até o sink e verifique se as tools respeitam a autorização do usuário final (não a do serviço).
- **Saída do modelo usada sem tratamento:** resposta do LLM renderizada como HTML/Markdown, executada (`eval`, SQL, shell) ou usada como URL.
- **Vazamento de dados entre usuários:** RAG/vector store sem filtro por tenant/owner; histórico de conversas acessível por ID (IDOR).
- **System prompt com segredos** (chaves, credenciais, regras de negócio sensíveis).
- **Agentes e MCP servers** com permissões excessivas.

Prompt injection sem um sink com impacto concreto é **INFORMATIVA**, não alta.

---

## ETAPA 7 — CONTROLE DE QUALIDADE

### 7.1 Filtro contra falsos positivos

Antes de classificar qualquer item como vulnerabilidade, responda:
1. A entrada é realmente controlável por um atacante?
2. O fluxo de dados foi confirmado?
3. Existe validação ou sanitização?
4. Existe autorização em outra camada (middleware, gateway, RLS)?
5. Existe feature flag ou configuração que impede a exploração?
6. A configuração necessária está habilitada?
7. O código está realmente em uso/produção (não é código morto, exemplo ou teste)?
8. Existe caminho alternativo que neutraliza a vulnerabilidade?
9. O comportamento depende de infraestrutura externa?
10. O impacto foi demonstrado pelo código?

Se não puder determinar: **NÃO CONFIRMADO — evidência insuficiente.**

### 7.2 Segunda passagem de cobertura

Antes do relatório, revise a matriz de endpoints e procure especificamente: endpoints, routers e handlers não classificados, recursos sem ownership, operações administrativas, GraphQL, server actions, webhooks, uploads, downloads, exports, imports, jobs, cron, workers, integrações externas, secrets, CI/CD, Docker, IaC, autenticação, recuperação de conta, MFA, CORS, CSRF, SSRF, XSS, injection, race conditions, business logic e LLM.

Se encontrar algo não analisado, analise antes de gerar o relatório.

---

## ETAPA 8 — CLASSIFICAÇÃO E FORMATO DOS ACHADOS

### Severidade
**CRÍTICA · ALTA · MÉDIA · BAIXA · INFORMATIVA**

Considere: impacto (confidencialidade, integridade, disponibilidade), pré-condições, privilégio necessário, interação do usuário, alcance, facilidade e exploração remota, e impacto multi-tenant.

### Confiança
**CONFIRMADO** (fluxo completo demonstrado no código) · **PROVÁVEL** (fluxo demonstrado, com dependência de configuração de runtime informada).
Itens abaixo disso não são achados: vão para a lista de NÃO CONFIRMADOS.

### Priorização
- **P1 — Correção imediata:** account takeover, acesso cross-tenant, execução remota, exposição massiva de dados, bypass administrativo, segredo comprometido, alteração de dados críticos, comprometimento de infraestrutura.
- **P2 — Alta prioridade:** impacto significativo com alguma pré-condição adicional.
- **P3 — Correção planejada:** riscos médios/baixos e hardening.

Informe CVSS apenas quando houver dados suficientes. **Não invente CVSS.**

### Formato de cada achado

```text
ACHADO: SEC-001
STATUS EM RELAÇÃO À BÁSICA: NOVO | PERSISTENTE
SEVERIDADE: ALTA
PRIORIDADE: P1
CONFIANÇA: CONFIRMADO
OWASP: A01:2025 — Broken Access Control
CWE: CWE-639
TTP: Authorization Abuse / BOLA

ARQUIVO:
src/api/orders/[id].ts:42-51

EVIDÊNCIA:
<trecho do código, com segredos mascarados>

SOURCE:
req.params.id

SINK:
database query

EXPLORAÇÃO:
<passo a passo conceitual>

PRÉ-CONDIÇÕES:
<condições>

IMPACTO:
<impacto>

POR QUE O CONTROLE ATUAL FALHA:
<explicação>

CORREÇÃO:
<correção específica para a stack detectada>
```

### Pontos fortes (obrigatório)

Registre os controles encontrados **e verificados**, sempre com evidência.

Ruim: *"Autorização parece correta."*
Bom: *"Os handlers X, Y e Z verificam `organization_id` antes da consulta, nas linhas A-B, C-D e E-F."*

### Status de cobertura

Use sempre um destes três status, por categoria:
- **VERIFICADO — nenhum achado confirmado** / **VERIFICADO — N achados**
- **NÃO APLICÁVEL — <justificativa>**
- **NÃO CONFIRMADO — evidência insuficiente**

Nunca transforme *"não encontrei"* em *"está seguro"*.

---

## ETAPA 9 — RELATÓRIO PDF

Gere `docs/security-audit/avancada/relatorio-auditoria-avancada.pdf`, a partir do `achados.json`, com o script gerador salvo em `docs/security-audit/avancada/` para regerar depois.

**Não sobrescreva** nada do relatório da auditoria básica.

**Geração:** sem instalação global. Use venv Python com `reportlab` + `matplotlib`, ou ferramenta equivalente da stack local. Se houver navegador headless, wkhtmltopdf ou pandoc, HTML → PDF também vale.

**Idioma:** pt-BR. **Formato:** A4, margens ~2 cm, cabeçalho e rodapé com o nome do relatório e o número da página.

**Paleta:**
- crítica `#B91C1C`
- alta `#EA580C`
- média `#D97706`
- baixa `#2563EB`
- informativa `#64748B`
- ponto forte `#059669`

### Seções, nesta ordem

1. **Capa:** `Relatório de Auditoria de Segurança Avançada — <nome do projeto>`, data, projeto, stack, escopo, metodologia (OWASP Top 10:2025 + TTPs), limitações.
2. **Resumo executivo:** total de achados por severidade, número de pontos fortes; gráfico de rosca por severidade; gráfico de barras por categoria OWASP.
3. **Evolução desde a auditoria básica:** tabela dos achados da básica com status (PERSISTENTE / CORRIGIDO / NÃO VERIFICÁVEL) e quantidade de achados novos. Omita se não houver auditoria básica, dizendo isso.
4. **Mapa de risco:** matriz Impacto × Probabilidade com os achados posicionados (quando houver dados suficientes).
5. **Pontos fortes:** controles comprovados, com evidência.
6. **Pontos fracos:** principais riscos, ordenados por prioridade.
7. **Matriz OWASP Top 10:2025:**

   | OWASP | Status | Achados | Observação |
   |---|---|---|---|
   | A01 Broken Access Control | | | |
   | A02 Security Misconfiguration | | | |
   | A03 Software Supply Chain Failures | | | |
   | A04 Cryptographic Failures | | | |
   | A05 Injection | | | |
   | A06 Insecure Design | | | |
   | A07 Authentication Failures | | | |
   | A08 Software or Data Integrity Failures | | | |
   | A09 Security Logging and Alerting Failures | | | |
   | A10 Mishandling of Exceptional Conditions | | | |

8. **Matriz de TTPs:**

   | TTP | Aplicável | Verificado | Achados |
   |---|---|---|---|
   | Reconhecimento | | | |
   | Credential Attacks | | | |
   | Session Attacks | | | |
   | Authorization Abuse | | | |
   | XSS | | | |
   | CSRF | | | |
   | CORS Abuse | | | |
   | Open Redirect | | | |
   | File Upload | | | |
   | Path Traversal | | | |
   | Deserialization | | | |
   | Prototype Pollution | | | |
   | HTTP Request Smuggling | | | |
   | HTTP Parameter Pollution | | | |
   | Race Conditions | | | |
   | Business Logic Abuse | | | |
   | SSRF | | | |
   | Supply Chain | | | |
   | LLM / Prompt Injection | | | |

9. **Cobertura:** resumo das matrizes de endpoints e de recursos (total, analisados, não aplicáveis, não confirmados).
10. **Achados detalhados:** tabela `ID | Severidade | OWASP | TTP | Arquivo:linha | Descrição` com chip de severidade colorido, seguida do detalhamento de cada achado no formato da Etapa 8.
11. **Não confirmados:** itens investigados sem evidência suficiente e o que seria necessário para confirmar (ex: teste dinâmico, acesso à config de produção).
12. **Recomendações P1, P2, P3:** específicas para a stack.
    Evite *"melhorar segurança"*. Prefira *"Adicionar verificação de `organization_id` no handler X antes da query Y e aplicar a mesma restrição em GET/PATCH/DELETE."*
13. **Issues para o GitHub** (última seção; ver Etapa 11).

---

## ETAPA 10 — VALIDAÇÃO DO PDF

Depois de gerar o PDF:
1. confirme que o arquivo existe e o número de páginas;
2. confirme que todas as seções estão presentes;
3. rasterize as páginas (ex: `pdftoppm`, PyMuPDF) e examine-as visualmente;
4. verifique gráficos (com legenda), tabelas legíveis, textos não cortados, ausência de páginas em branco inesperadas, cabeçalho, rodapé e numeração;
5. confirme que nenhum segredo aparece completo;
6. corrija os problemas, gere novamente e faça uma validação final.

---

## ETAPA 11 — ISSUES PARA O GITHUB

No final do PDF, para cada achado acionável, gere o texto completo de uma issue em Markdown, pronto para copiar e colar. Agrupe achados triviais relacionados (ex: vários defaults de segredo do mesmo tema) para não gerar spam.

Para achados **PERSISTENTES** da auditoria básica, indique na issue que o problema já havia sido apontado antes.

**Não abra issues no GitHub.** Elas ficam apenas como texto no PDF, para o usuário revisar e decidir onde registrar.

**Formato de cada issue:**

~~~markdown
--- ISSUE 1 ---

# [Segurança] <descrição curta>

Labels: security, <severidade>

## Descrição
...

## Por que é explorável
...

## Evidência

**Arquivo:** `arquivo:linha`

```
<trecho, com segredos mascarados>
```

## Impacto
...

## Correção sugerida
...

## Critérios de aceite
- [ ] correção aplicada no backend
- [ ] teste de regressão criado
- [ ] nenhum caminho alternativo permanece vulnerável
- [ ] segredo rotacionado (quando aplicável)

--- FIM ISSUE 1 ---
~~~

---

## SAÍDA FINAL NO CHAT

Ao terminar, entregue:

1. **Resumo:** stack, arquitetura, superfície de ataque, número de arquivos, endpoints/handlers e recursos analisados, total de achados e distribuição por severidade.
2. **Evolução:** achados da básica corrigidos / persistentes / novos.
3. **Achados:** arquivo por arquivo e linha por linha, com ID, severidade, confiança, OWASP, CWE, TTP, descrição e impacto.
4. **Pontos fortes:** com evidência.
5. **Cobertura OWASP e TTP:** status de cada categoria.
6. **Cobertura de endpoints:** total, analisados, não aplicáveis, não confirmados.
7. **Arquivos gerados:** caminhos do PDF, script gerador, `achados.json` e arquivos auxiliares.
8. **Limitações:** o que não pôde ser verificado e o que depende de configuração externa, runtime, infraestrutura ou teste dinâmico.

---

## REGRA FINAL

A qualidade da auditoria é medida por **COBERTURA + EVIDÊNCIA + RASTREABILIDADE + EXPLORABILIDADE**, não pela quantidade de vulnerabilidades.

É melhor entregar *2 vulnerabilidades confirmadas + 30 controles comprovadamente corretos* do que *15 vulnerabilidades especulativas*.

Nunca invente uma vulnerabilidade para preencher uma categoria. Nunca omita uma categoria porque ela não teve achados. A auditoria deve mostrar tanto *o que está vulnerável* quanto *o que foi procurado e está protegido*.

---

## CRITÉRIO DE CONCLUSÃO

Só finalize quando todos os itens estiverem marcados:

- [ ] resultados da auditoria básica lidos e status de cada achado atualizado (ou ausência registrada)
- [ ] `achados.json` atualizado e completo
- [ ] stack, arquitetura e superfície de ataque identificadas
- [ ] matriz de endpoints completa, todos os handlers classificados
- [ ] modelo de identidade e matriz de recursos preenchidos
- [ ] autenticação, autorização e isolamento de tenant analisados
- [ ] OWASP A01–A10:2025 cobertos
- [ ] TTPs aplicáveis cobertas
- [ ] frontend e backend cruzados
- [ ] segredos procurados, incluindo histórico Git, bundles e source maps
- [ ] infraestrutura e CI/CD analisados
- [ ] dependências analisadas
- [ ] seção de IA/LLM avaliada (ou marcada como não aplicável)
- [ ] falsos positivos revisados e segunda passagem de cobertura feita
- [ ] pontos fortes documentados com evidência
- [ ] PDF gerado, validado visualmente e sem segredos completos
- [ ] textos das issues gerados no PDF (sem abrir nenhuma no GitHub)
- [ ] arquivos gerados listados e limitações documentadas
