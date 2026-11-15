# Como a IA foi usada neste projeto

> Rascunho inicial. Anna: revise, ajuste com as suas palavras e preencha as partes marcadas antes de publicar.

## Divisão do trabalho

| Quem | O quê |
|---|---|
| Anna | Problema (vivência no RH), escopo, regras de negócio do agente, o que é sensível e deve ir para uma pessoa, métricas e meta de cada uma, revisão das respostas, testes com voluntários |
| Claude (Anthropic) | Rascunho do manual fictício e do gabarito, primeira versão dos prompts, código do app React, do script Python e do gerador dos fluxos do n8n |
| GPT-4o mini (dentro do produto, pelo n8n) | Responder às perguntas (agente atendente) e escrever o relatório semanal (agente analista) |

## Como eu pedi

* Comecei pelo problema e pelas regras, não pelo código: o que o agente pode e não pode fazer, e por quê.
* Pedi que cada regra do prompt viesse com o motivo, para eu conseguir defender cada uma.
* Pedi que contas ficassem em código e interpretação ficasse com a IA, para não depender do modelo para somar.

## O que a IA errou e eu corrigi

_Preencher durante a construção. Exemplos do tipo de coisa a registrar:_
* _Pergunta X: o agente respondeu sem citar a seção. Ajuste no prompt: ..._
* _O gráfico não aparecia porque ... Correção: ..._
* _..._

## O que mudou da versão 1 para a versão 2 do prompt

_Preencher depois de rodar o `avaliar.py`: qual pergunta errou, qual regra foi mudada e o resultado da nova rodada._

## Cuidados

* A chave da API nunca foi colocada no código nem no chat com a IA.
* Nenhum dado real de empresa ou de pessoa foi usado.
* Toda resposta do agente foi conferida contra o gabarito, não aceita no olho.

## Decisão registrada: troca do modelo

O plano era usar o Gemini. Na primeira execução, o modelo escolhido tinha sido descontinuado para contas novas. Com o modelo novo, as chamadas ficavam presas: o painel do Google mostrou que a camada gratuita permite 5 pedidos por minuto e 20 por dia, e o agente faz de 2 a 3 chamadas por pergunta. Só o teste das 40 perguntas pediria cerca de 100 chamadas. A solução foi usar o GPT-4o mini pelos créditos do n8n, sem mudar o agente, as ferramentas nem o resto do fluxo.
