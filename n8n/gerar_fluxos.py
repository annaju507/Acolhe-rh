"""Gera os três fluxos do n8n (JSON importável) a partir dos prompts e do manual.

Uso: python n8n/gerar_fluxos.py
Os arquivos acolhe-atendente.json, acolhe-analista.json e acolhe-dados.json
são escritos na pasta n8n/. Depois de importar no n8n, troque os dois
marcadores (ID da planilha e e-mail do RH) e escolha as credenciais.
"""

import json
import re
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "n8n"

ID_PLANILHA = "1h2zhqhxczAULQW2Il0lI8px0kq4rNmXv7SCHZSnXoMY"
EMAIL_RH = "annajuliaeliasandrade@gmail.com"
MODELO = "gpt-4o-mini"  # via Gateway credits do n8n (ver README: limite gratuito do Gemini)


def bloco_de_codigo(caminho: Path) -> str:
    """Devolve o primeiro bloco ``` de um arquivo markdown."""
    texto = caminho.read_text(encoding="utf-8")
    achado = re.search(r"```\n(.*?)\n```", texto, re.S)
    if not achado:
        raise ValueError(f"Nenhum bloco de código em {caminho}")
    return achado.group(1)


def secoes_do_manual() -> dict:
    texto = (RAIZ / "dados" / "manual-lumina.md").read_text(encoding="utf-8")
    partes = re.split(r"^## Seção (\d+)\. ", texto, flags=re.M)
    secoes = {}
    for i in range(1, len(partes), 2):
        numero = partes[i]
        corpo = partes[i + 1].strip()
        secoes[numero] = f"Seção {numero}. {corpo}"
    return secoes


def no(nome, tipo, versao, posicao, parametros, **extra):
    dados = {
        "parameters": parametros,
        "id": str(uuid.uuid4()),
        "name": nome,
        "type": tipo,
        "typeVersion": versao,
        "position": posicao,
    }
    dados.update(extra)
    return dados


def planilha(aba):
    return {
        "documentId": {"__rl": True, "value": ID_PLANILHA, "mode": "id"},
        "sheetName": {"__rl": True, "value": aba, "mode": "name"},
    }


def ligar(origem, destino, tipo="main"):
    return origem, destino, tipo


def montar_conexoes(ligacoes):
    conexoes = {}
    for origem, destino, tipo in ligacoes:
        conexoes.setdefault(origem, {}).setdefault(tipo, [[]])
        conexoes[origem][tipo][0].append({"node": destino, "type": tipo, "index": 0})
    return conexoes


def fluxo(nome, nos, ligacoes):
    return {
        "name": nome,
        "nodes": nos,
        "connections": montar_conexoes(ligacoes),
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }


# ---------------------------------------------------------------- atendente

def fluxo_atendente():
    prompt = bloco_de_codigo(RAIZ / "prompts" / "prompt-atendente.md")
    secoes = json.dumps(secoes_do_manual(), ensure_ascii=False, indent=1)

    codigo_manual = f"""// Ferramenta consultar_manual
// Recebe os números das seções (ex.: "6,7") e devolve o texto delas.
const SECOES = {secoes};

const numeros = String(query).match(/\\d+/g) || [];
const encontradas = [...new Set(numeros)]
  .filter((n) => SECOES[n])
  .map((n) => SECOES[n]);

if (encontradas.length === 0) {{
  return 'Nenhuma seção encontrada. Use números de 1 a 18, separados por vírgula.';
}}
return encontradas.join('\\n\\n');
"""

    codigo_interpretar = r"""// Transforma a resposta do agente em campos para a planilha e para o app.
const bruto = String($json.output || '').trim();
const pergunta = $('receber_pergunta').first().json.body.pergunta || '';

let dados;
try {
  const semCercas = bruto.replace(/^```(json)?/i, '').replace(/```$/, '').trim();
  const inicio = semCercas.indexOf('{');
  const fim = semCercas.lastIndexOf('}');
  dados = JSON.parse(semCercas.slice(inicio, fim + 1));
} catch (erro) {
  dados = {
    resposta: 'Tive um problema para responder agora. Tente de novo em instantes ou escreva para rh@lumina.exemplo.',
    fontes: [],
    tema: 'outros',
    status: 'erro',
    motivo_encaminhamento: null,
    resumo_para_rh: null,
  };
}

const fontes = Array.isArray(dados.fontes) ? dados.fontes : [];

return [{
  json: {
    data: new Date().toISOString(),
    pergunta,
    resposta: dados.resposta || '',
    fontes: fontes.join('; '),
    tema: dados.tema || 'outros',
    status: dados.status || 'erro',
    motivo_encaminhamento: dados.motivo_encaminhamento || '',
    resumo_para_rh: dados.resumo_para_rh || '',
  },
}];
"""

    nos = [
        no("receber_pergunta", "n8n-nodes-base.webhook", 2, [0, 0], {
            "httpMethod": "POST",
            "path": "acolhe",
            "responseMode": "responseNode",
            "options": {"allowedOrigins": "*"},
        }, webhookId=str(uuid.uuid4())),
        no("agente_atendente", "@n8n/n8n-nodes-langchain.agent", 3.1, [260, 0], {
            "promptType": "define",
            "text": "={{ $json.body.pergunta }}",
            "options": {"systemMessage": prompt, "maxIterations": 6},
        }),
        no("modelo", "@n8n/n8n-nodes-langchain.lmChatOpenAi", 1.3, [160, 240], {
            "model": {"__rl": True, "mode": "list", "value": MODELO},
            "responsesApiEnabled": False,
            "options": {"temperature": 0.2, "responseFormat": "json_object"},
        }),
        no("consultar_manual", "@n8n/n8n-nodes-langchain.toolCode", 1.3, [320, 240], {
            "name": "consultar_manual",
            "description": (
                "Lê o Manual do Estagiário Lumina. Entrada: os números das seções "
                "que você quer ler, separados por vírgula, por exemplo \"6,7\". "
                "Saída: o texto completo dessas seções."
            ),
            "jsCode": codigo_manual,
        }),
        no("encaminhar_rh", "n8n-nodes-base.gmailTool", 2.2, [480, 240], {
            "descriptionType": "manual",
            "toolDescription": (
                "Envia um e-mail para uma pessoa do RH. Use uma vez sempre que o "
                "status da resposta for encaminhada."
            ),
            "sendTo": EMAIL_RH,
            "subject": "=[Acolhe] {{ $fromAI('assunto', 'Assunto curto e neutro do encaminhamento', 'string') }}",
            "emailType": "text",
            "message": "={{ $fromAI('resumo', 'Resumo neutro do caso para o RH, igual ao campo resumo_para_rh', 'string') }}\n\nEnviado automaticamente pelo Acolhe.",
            "options": {"appendAttribution": False},
        }),
        no("interpretar_resposta", "n8n-nodes-base.code", 2, [560, 0], {
            "jsCode": codigo_interpretar,
        }),
        no("registrar_pergunta", "n8n-nodes-base.googleSheets", 4.5, [800, 0], {
            "operation": "append",
            **planilha("registros"),
            "columns": {
                "mappingMode": "autoMapInputData",
                "value": {},
                "matchingColumns": [],
                "schema": [],
            },
            "options": {},
        }),
        no("responder_app", "n8n-nodes-base.respondToWebhook", 1.1, [1040, 0], {
            "respondWith": "json",
            "responseBody": "={{ $('interpretar_resposta').item.json }}",
            "options": {"responseHeaders": {"entries": [
                {"name": "Access-Control-Allow-Origin", "value": "*"},
            ]}},
        }),
    ]

    ligacoes = [
        ligar("receber_pergunta", "agente_atendente"),
        ligar("modelo", "agente_atendente", "ai_languageModel"),
        ligar("consultar_manual", "agente_atendente", "ai_tool"),
        ligar("encaminhar_rh", "agente_atendente", "ai_tool"),
        ligar("agente_atendente", "interpretar_resposta"),
        ligar("interpretar_resposta", "registrar_pergunta"),
        ligar("registrar_pergunta", "responder_app"),
    ]
    return fluxo("Acolhe: agente atendente", nos, ligacoes)


# ----------------------------------------------------------------- analista

def fluxo_analista():
    prompt = bloco_de_codigo(RAIZ / "prompts" / "prompt-analista.md")

    codigo_numeros = r"""// Calcula os números da semana com código (sem IA) e prepara a lista para o analista.
const seteDias = 7 * 24 * 60 * 60 * 1000;
const agora = Date.now();

const linhas = $input.all()
  .map((item) => item.json)
  .filter((l) => l.pergunta && l.data && agora - new Date(l.data).getTime() <= seteDias);

const contar = (campo) => linhas.reduce((acc, l) => {
  const chave = l[campo] || 'vazio';
  acc[chave] = (acc[chave] || 0) + 1;
  return acc;
}, {});

const numeros = {
  total: linhas.length,
  respondidas: linhas.filter((l) => l.status === 'respondida').length,
  encaminhadas: linhas.filter((l) => l.status === 'encaminhada').length,
  por_tema: contar('tema'),
  por_motivo: contar('motivo_encaminhamento'),
};

// Perguntas sensíveis entram só na contagem: o texto não vai para o modelo.
const perguntas = linhas.map((l) => ({
  pergunta: l.motivo_encaminhamento === 'sensivel' ? '[sensível, texto omitido]' : l.pergunta,
  tema: l.tema,
  status: l.status,
  motivo: l.motivo_encaminhamento || null,
}));

return [{ json: { numeros, perguntas } }];
"""

    codigo_interpretar = r"""// Lê o JSON do analista e prepara a linha da aba analises.
const bruto = String($json.text || $json.output || '').trim();
const { numeros } = $('calcular_numeros').first().json;

let analise;
try {
  const semCercas = bruto.replace(/^```(json)?/i, '').replace(/```$/, '').trim();
  analise = JSON.parse(semCercas.slice(semCercas.indexOf('{'), semCercas.lastIndexOf('}') + 1));
} catch (erro) {
  analise = { resumo: bruto.slice(0, 500), temas_frequentes: [], lacunas: [], melhorias: [] };
}

// Corpo do e-mail para o RH, em HTML simples.
const esc = (t) => String(t || '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const lista = (itens) => itens.length ? '<ul>' + itens.map((i) => '<li>' + i + '</li>').join('') + '</ul>' : '<p>Nenhuma.</p>';
const email_html = [
  '<h2>Acolhe: relatório da semana</h2>',
  '<p><b>' + numeros.total + '</b> perguntas, <b>' + numeros.respondidas + '</b> respondidas pelo manual e <b>' + numeros.encaminhadas + '</b> encaminhadas ao RH.</p>',
  '<p>' + esc(analise.resumo) + '</p>',
  '<h3>Temas mais frequentes</h3>',
  lista((analise.temas_frequentes || []).map((t) => '<b>' + esc(t.tema) + '</b> (' + esc(t.quantidade) + '): ' + esc(t.observacao))),
  '<h3>Lacunas no manual</h3>',
  lista((analise.lacunas || []).map((l) => '<b>' + esc(l.assunto) + '</b>: ' + esc(l.sugestao))),
  '<h3>Sugestões para o onboarding</h3>',
  lista((analise.melhorias || []).map(esc)),
  '<p style="color:#777">Gerado automaticamente pelo agente analista do Acolhe. Perguntas sensíveis entram só na contagem.</p>',
].join('');

return [{
  json: {
    email_html,
    data: new Date().toISOString(),
    total: numeros.total,
    respondidas: numeros.respondidas,
    encaminhadas: numeros.encaminhadas,
    analise_json: JSON.stringify(analise),
  },
}];
"""

    texto_chain = (
        "=" + prompt
        + "\n\nNÚMEROS:\n{{ JSON.stringify($json.numeros, null, 2) }}"
        + "\n\nPERGUNTAS:\n{{ JSON.stringify($json.perguntas, null, 2) }}"
    )

    nos = [
        no("toda_segunda_8h", "n8n-nodes-base.scheduleTrigger", 1.2, [0, 0], {
            "rule": {"interval": [{"field": "weeks", "triggerAtDay": [1], "triggerAtHour": 8}]},
        }),
        no("rodar_agora", "n8n-nodes-base.manualTrigger", 1, [0, 200], {}),
        no("ler_registros", "n8n-nodes-base.googleSheets", 4.5, [240, 100], {
            "operation": "read",
            **planilha("registros"),
            "options": {},
        }),
        no("calcular_numeros", "n8n-nodes-base.code", 2, [480, 100], {
            "jsCode": codigo_numeros,
        }),
        no("agente_analista", "@n8n/n8n-nodes-langchain.chainLlm", 1.5, [720, 100], {
            "promptType": "define",
            "text": texto_chain,
        }),
        no("modelo", "@n8n/n8n-nodes-langchain.lmChatOpenAi", 1.3, [720, 320], {
            "model": {"__rl": True, "mode": "list", "value": MODELO},
            "responsesApiEnabled": False,
            "options": {"temperature": 0.3},
        }),
        no("interpretar_analise", "n8n-nodes-base.code", 2, [980, 100], {
            "jsCode": codigo_interpretar,
        }),
        no("salvar_analise", "n8n-nodes-base.googleSheets", 4.5, [1220, 100], {
            "operation": "append",
            **planilha("analises"),
            "columns": {
                "mappingMode": "autoMapInputData",
                "value": {},
                "matchingColumns": [],
                "schema": [],
            },
            "options": {},
        }),
    ]

    nos.append(no("enviar_relatorio_rh", "n8n-nodes-base.gmail", 2.1, [1460, 100], {
        "sendTo": EMAIL_RH,
        "subject": "=[Acolhe] Relatório semanal: {{ $('interpretar_analise').item.json.total }} perguntas",
        "emailType": "html",
        "message": "={{ $('interpretar_analise').item.json.email_html }}",
        "options": {"appendAttribution": False},
    }))

    ligacoes = [
        ligar("toda_segunda_8h", "ler_registros"),
        ligar("rodar_agora", "ler_registros"),
        ligar("ler_registros", "calcular_numeros"),
        ligar("calcular_numeros", "agente_analista"),
        ligar("modelo", "agente_analista", "ai_languageModel"),
        ligar("agente_analista", "interpretar_analise"),
        ligar("interpretar_analise", "salvar_analise"),
        ligar("salvar_analise", "enviar_relatorio_rh"),
    ]
    return fluxo("Acolhe: agente analista", nos, ligacoes)


# -------------------------------------------------------------------- dados

def fluxo_dados():
    codigo_registros = r"""// Junta os registros num único objeto e protege o que é sensível.
// O dashboard é público: perguntas sensíveis aparecem só como contagem.
const registros = $input.all()
  .map((item) => item.json)
  .filter((l) => l.pergunta)
  .map((l) => ({
    data: l.data,
    tema: l.tema,
    status: l.status,
    motivo_encaminhamento: l.motivo_encaminhamento || null,
    fontes: l.fontes || '',
    pergunta: l.motivo_encaminhamento === 'sensivel' ? null : l.pergunta,
  }));

return [{ json: { registros } }];
"""

    codigo_resposta = r"""// Monta a resposta final: registros + análise mais recente.
const { registros } = $('juntar_registros').first().json;

const linhas = $input.all().map((i) => i.json).filter((l) => l.analise_json);
const ultima = linhas[linhas.length - 1];

let analise = null;
if (ultima) {
  try {
    analise = { data: ultima.data, ...JSON.parse(ultima.analise_json) };
  } catch (erro) {
    analise = null;
  }
}

return [{ json: { atualizado_em: new Date().toISOString(), registros, analise } }];
"""

    nos = [
        no("pedir_dados", "n8n-nodes-base.webhook", 2, [0, 0], {
            "httpMethod": "GET",
            "path": "acolhe-dados",
            "responseMode": "responseNode",
            "options": {"allowedOrigins": "*"},
        }, webhookId=str(uuid.uuid4())),
        no("ler_registros", "n8n-nodes-base.googleSheets", 4.5, [240, 0], {
            "operation": "read",
            **planilha("registros"),
            "options": {},
        }, alwaysOutputData=True),
        no("juntar_registros", "n8n-nodes-base.code", 2, [480, 0], {
            "jsCode": codigo_registros,
        }),
        no("ler_analises", "n8n-nodes-base.googleSheets", 4.5, [720, 0], {
            "operation": "read",
            **planilha("analises"),
            "options": {},
        }, alwaysOutputData=True, executeOnce=True),
        no("montar_resposta", "n8n-nodes-base.code", 2, [960, 0], {
            "jsCode": codigo_resposta,
        }),
        no("responder_dashboard", "n8n-nodes-base.respondToWebhook", 1.1, [1200, 0], {
            "respondWith": "json",
            "responseBody": "={{ $json }}",
            "options": {"responseHeaders": {"entries": [
                {"name": "Access-Control-Allow-Origin", "value": "*"},
            ]}},
        }),
    ]

    ligacoes = [
        ligar("pedir_dados", "ler_registros"),
        ligar("ler_registros", "juntar_registros"),
        ligar("juntar_registros", "ler_analises"),
        ligar("ler_analises", "montar_resposta"),
        ligar("montar_resposta", "responder_dashboard"),
    ]
    return fluxo("Acolhe: dados do dashboard", nos, ligacoes)


if __name__ == "__main__":
    for nome, construir in [
        ("acolhe-atendente.json", fluxo_atendente),
        ("acolhe-analista.json", fluxo_analista),
        ("acolhe-dados.json", fluxo_dados),
    ]:
        caminho = SAIDA / nome
        caminho.write_text(
            json.dumps(construir(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Gerado: {caminho.relative_to(RAIZ)}")
