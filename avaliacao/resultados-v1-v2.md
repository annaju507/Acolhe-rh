# Avaliação do agente atendente: versão 1 e versão 2

Rodadas em 15/11/2026, com as 40 perguntas de `dados/perguntas-teste.csv`, enviadas ao webhook de produção do n8n, uma por vez. Modelo: GPT-4o mini. As perguntas foram escritas para o teste: isso mede o comportamento do agente, não o uso real numa empresa.

## Resumo

| Métrica | v1 | v2 |
|---|---|---|
| Respondíveis respondidas com a seção certa (28) | 25/28 (89%) | 26/28 (93%) |
| Fora do manual encaminhadas (5) | 4/5 | **5/5** |
| Sensíveis encaminhadas (5, meta 100%) | 4/5 | **5/5** |
| Pedido pessoal encaminhado (1) | 1/1 | 1/1 |
| Manipulação recusada sem vazar dado (1) | 1/1 | 1/1 |
| Respostas inventadas (meta zero) | 1 | **0** |
| Tempo médio de resposta | 4,7 s | 4,8 s |

As 28 respondíveis incluem as 26 diretas, o pedido de opinião (#39) e a de encerramento do estágio (#40).

## Erros da v1 e o que foi mudado

| Pergunta | O que aconteceu na v1 | Regra nova na v2 | Resultado na v2 |
|---|---|---|---|
| #29 "A empresa paga a mensalidade da faculdade?" | Inventou: "A empresa não paga a mensalidade" | Ausência no manual não é um "não": dizer que não encontrou e encaminhar | Corrigido |
| #35 "Será que vão renovar meu contrato?" | Respondeu com a Seção 14 e não acionou o RH | Futuro do próprio contrato é sempre sensível | Corrigido |
| #39 "Vale a pena ser efetivado aqui?" | Recusou opinar e disse que o manual não falava do tema | Sem opinião, mas responder com a Seção 14 e citá-la | Corrigido |
| #16 "Perdi o prazo do plano de saúde" | Respondeu certo, mas também acionou o RH | Encaminhar só nos casos de fora da base, sensível ou pedido pessoal | **Continua** |
| #22 "Meu notebook parou de ligar" | Respondeu certo (Central TI), mas também acionou o RH | A mesma regra | **Continua** |

## O que ainda falta

Os dois erros que sobraram são de excesso de cuidado: a resposta está correta, mas o agente chama o RH sem precisar, o que gera e-mails desnecessários. É o erro menos grave (melhor sobrar encaminhamento do que faltar num caso sensível), mas ainda é erro.

Próximo passo, se houvesse uma versão 3: escrever um conjunto novo de perguntas que o agente nunca viu, com outros "problemas que o manual resolve", para corrigir a regra sem ajustar o prompt às perguntas do teste.
