# Auditoria de Segurança com IA

Prompts prontos para o seu agente de IA (Claude Code, Codex, Cursor, Gemini CLI, Copilot...) **procurar problemas de segurança no seu código e no seu repositório** e entregar um **relatório em PDF**, com os achados, os pontos fortes e as issues prontas para o GitHub.

Feito para quem cria aplicações com IA ("vibe coding") e quer saber, de forma simples, se deixou alguma porta aberta.

---

## O que tem aqui

| Arquivo | O que faz | Quando usar |
|---|---|---|
| [`prompts/01-auditoria-basica.md`](prompts/01-auditoria-basica.md) | Procura as **5 falhas mais comuns** em apps feitos com IA: banco sem tranca (RLS/tenant), permissão só no navegador, IDOR, chaves expostas e XSS. | **Sempre primeiro.** Rápida e direta. |
| [`prompts/02-auditoria-avancada.md`](prompts/02-auditoria-avancada.md) | Auditoria completa: **OWASP Top 10:2025**, técnicas de ataque (TTPs), supply chain, CI/CD, infraestrutura e apps com LLM. Também compara com o resultado da básica. | **Depois** da básica, de preferência depois de corrigir o que ela encontrou. |

**Resultados gerados no seu projeto:**

```text
docs/security-audit/relatorio-auditoria-seguranca.pdf               ← básica
docs/security-audit/avancada/relatorio-auditoria-avancada.pdf       ← avançada
```

---

## Antes de começar

- Um agente de IA que **lê arquivos e roda comandos** no seu computador (veja a lista abaixo).
- **Python 3** instalado (é usado para gerar o PDF, dentro de um ambiente isolado).
- **Git** (para analisar o histórico em busca de senhas antigas).
- Faça um **commit** do seu trabalho antes. Assim fica fácil ver exatamente o que o agente criou.

---

## Como rodar (3 passos)

**1. Baixe este repositório** em qualquer pasta do seu computador.

**2. Abra o seu agente na raiz do projeto que você quer auditar** (não nesta pasta).

**3. Peça para ele executar o prompt.** Funciona de dois jeitos em qualquer plataforma:

- **Jeito A, apontando o arquivo:**

  ```text
  Leia o arquivo /caminho/para/auditoria-AI/prompts/01-auditoria-basica.md e execute todas as instruções dele neste projeto.
  ```

- **Jeito B, colando o conteúdo:** abra o arquivo `.md`, copie tudo e cole na conversa com o agente.

Quando a básica terminar, repita o passo 3 com `02-auditoria-avancada.md`.

> Dica: se o agente não conseguir ler arquivos fora do projeto, copie a pasta `prompts/` para dentro do seu projeto ou use o Jeito B.

### Por plataforma

| Plataforma | Como fazer |
|---|---|
| **Claude Code** (terminal ou app) | Entre na pasta do projeto, rode `claude` e use o Jeito A ou B. Aceite as permissões para ler arquivos e rodar Python. |
| **Codex CLI** (OpenAI) | Entre na pasta do projeto, rode `codex` e use o Jeito A ou B. Se ele bloquear a leitura fora do projeto, use o Jeito B. |
| **Cursor / Windsurf** | Abra o projeto, abra o chat no modo **Agent** e use o Jeito A ou B. |
| **Gemini CLI** | Entre na pasta do projeto, rode `gemini` e use o Jeito A ou B. |
| **GitHub Copilot** (VS Code) | Abra o chat no modo **Agent** e use o Jeito B. |
| **Outras** | Qualquer agente que leia arquivos e execute comandos funciona com o Jeito B. |

---

## Exemplos de relatório

Quer ver o resultado antes de rodar? A pasta [`exemplos/`](exemplos/) tem dois relatórios de um projeto **fictício** (o "TaskFlow", um SaaS de tarefas feito com Next.js + Supabase):

- [`exemplos/exemplo-relatorio-basico.pdf`](exemplos/exemplo-relatorio-basico.pdf)
- [`exemplos/exemplo-relatorio-avancado.pdf`](exemplos/exemplo-relatorio-avancado.pdf)

Os dados ficam em `exemplos/dados/*.json` e o script que gera os PDFs em `exemplos/gerador/gerar_relatorio.py`. É o mesmo formato que o prompt avançado pede ao agente: os achados são salvos em JSON e o PDF é gerado a partir deles.

---

## Como corrigir os problemas encontrados

Com o relatório em mãos, peça ao seu agente para corrigir. A auditoria não altera o seu código: a correção é um passo separado, que você controla.

**1. Comece pelos mais graves.** Corrija primeiro os itens **P1** (críticos e altos) e depois P2 e P3.

**2. Corrija um problema por vez,** em uma branch separada. Fica mais fácil revisar e desfazer se algo der errado.

**3. Use um pedido como este** (troque o ID e o caminho do relatório):

```text
Leia o relatório docs/security-audit/relatorio-auditoria-seguranca.pdf e corrija o achado SEC-001.

Regras:
- Crie uma branch chamada fix/sec-001 antes de alterar qualquer coisa.
- Explique primeiro o que vai mudar e por quê, e espere a minha confirmação.
- Corrija no backend (servidor/banco), não só na tela.
- Procure o mesmo problema em outras rotas e arquivos parecidos e corrija também.
- Crie um teste que prove que a falha não acontece mais.
- Não altere nada que não esteja relacionado a este achado.
- No final, mostre o que foi alterado e como eu posso testar.
```

Outros pedidos úteis:

```text
Liste os achados P1 do relatório e monte um plano de correção, em ordem, sem alterar o código ainda.
```

```text
Use o texto da ISSUE 3 do final do relatório como especificação e implemente a correção, cumprindo todos os critérios de aceite.
```

```text
Revise a correção que você acabou de fazer como um atacante: ainda existe algum caminho para explorar o mesmo problema?
```

**4. Revise o que mudou** antes de aceitar (`git diff`). Se não entender alguma alteração, peça ao agente para explicar.

**5. Chaves e senhas expostas exigem uma ação sua:** gere uma nova chave no painel do serviço (Supabase, Stripe, OpenAI...) e revogue a antiga. Só tirar do código não basta. Depois peça ao agente para passar a ler a chave de variável de ambiente.

**6. Rode a auditoria de novo** depois das correções. A avançada mostra o que foi corrigido, o que continua e o que é novo.

---

## Dicas importantes

- **Leia o relatório com senso crítico.** A IA pode errar. Cada achado tem `arquivo:linha`: abra e confira.
- **Achou uma chave ou senha exposta? Troque (rotacione) ela agora.** Apagar do código não resolve, porque ela continua no histórico do Git.
- **Os prompts não abrem issues no GitHub.** O texto de cada issue vem pronto no final do PDF, para você copiar e colar. Em repositório **público**, uma issue deixa a falha visível para qualquer pessoa antes da correção: prefira o **GitHub Security Advisory** (aba *Security → Advisories*), que é privado.
- **Não publique o relatório.** Adicione `docs/security-audit/` ao seu `.gitignore` se o repositório for público.
- **Projetos grandes consomem muitos tokens.** A avançada pode levar bastante tempo. Se for preciso, peça para o agente auditar um módulo ou pasta por vez.
- **Use o modelo mais capaz que você tiver.** Auditoria de segurança se beneficia muito de modelos de raciocínio mais fortes.
- **Rode de novo depois de corrigir.** A avançada compara com o resultado anterior e mostra o que foi corrigido.

---

## O que estes prompts não fazem

- Não substituem um **pentest** profissional nem testes dinâmicos contra a aplicação rodando.
- Não atacam nada: a análise é feita **lendo o código e as configurações**.
- Não corrigem o código sozinhos. Você decide o que corrigir, depois, com base no relatório e nas issues.

---

Projeto educacional para ajudar quem desenvolve com IA a criar aplicações mais seguras. Contribuições e sugestões são bem-vindas.
