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
COLUNAS_ANALISES = ["data", "total", "respondidas", "encaminhadas", "analise_json"]
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

    codigo_interpretar = r"""// Lê o JSON do analista e prepara a linha da aba analises e o e-mail do RH.
const bruto = String($json.text || $json.output || '').trim();
const { numeros } = $('calcular_numeros').first().json;

let analise;
try {
  const semCercas = bruto.replace(/^```(json)?/i, '').replace(/```$/, '').trim();
  analise = JSON.parse(semCercas.slice(semCercas.indexOf('{'), semCercas.lastIndexOf('}') + 1));
} catch (erro) {
  analise = { resumo: bruto.slice(0, 500), temas_frequentes: [], lacunas: [], melhorias: [] };
}

// ---------- e-mail em HTML (estilos inline, para funcionar no Gmail)
const esc = (t) => String(t ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const LIL = '#7c5cbf', LIL2 = '#efe9fb', AQ = '#14b8c8', AQ2 = '#dff7f9', INK = '#24212e', SOFT = '#6b6678', LINE = '#e6e1ef';
const NOMES = { admissao: 'Admissão', primeira_semana: 'Primeira semana', jornada_ponto: 'Jornada e ponto', provas: 'Provas', bolsa: 'Bolsa', transporte: 'Transporte', beneficios: 'Benefícios', recesso: 'Recesso', faltas_atestados: 'Faltas e atestados', hibrido_equipamento: 'Híbrido e equipamento', acessos_ti: 'Acessos e TI', avaliacao: 'Avaliação', efetivacao: 'Efetivação', conduta: 'Conduta', etica_sensivel: 'Ética e sensíveis', desligamento: 'Fim do estágio', outros: 'Outros', pedido_pessoal: 'Pedido pessoal' };
const pct = (a, b) => (b ? Math.round((a / b) * 100) : 0);
const hoje = new Date().toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo' });

const kpi = (rotulo, valor, detalhe, fundo, cor) =>
  `<td width="25%" style="padding:6px"><div style="background:${fundo};border-radius:14px;padding:14px 16px;border:1px solid ${LINE}">
   <div style="font-size:12px;color:${cor === '#fff' ? '#ece5fb' : SOFT}">${rotulo}</div>
   <div style="font-size:30px;font-weight:700;color:${cor};margin-top:2px">${valor}</div>
   <div style="font-size:11px;color:${cor === '#fff' ? '#ece5fb' : SOFT}">${detalhe}</div></div></td>`;

const porTema = Object.entries(numeros.por_tema || {}).sort((a, b) => b[1] - a[1]).slice(0, 8);
const max = porTema.length ? porTema[0][1] : 1;
const barras = porTema.map(([t, n]) =>
  `<tr><td style="font-size:13px;color:${SOFT};padding:4px 10px 4px 0;white-space:nowrap;text-align:right" width="150">${esc(NOMES[t] || t)}</td>
   <td style="padding:4px 0"><div style="background:${LIL};height:12px;border-radius:3px;width:${Math.max(4, (n / max) * 100)}%"></div></td>
   <td style="font-size:13px;font-weight:700;padding-left:8px" width="30">${n}</td></tr>`).join('');

const motivos = numeros.por_motivo || {};
const linhaMotivo = (rotulo, n) =>
  `<tr><td style="font-size:13px;padding:5px 0">${rotulo}</td><td style="font-size:13px;font-weight:700;text-align:right">${n || 0}</td></tr>
   <tr><td colspan="2"><div style="background:${LIL2};height:7px;border-radius:9px"><div style="background:${AQ};height:7px;border-radius:9px;width:${pct(n || 0, numeros.encaminhadas || 1)}%"></div></div></td></tr>`;

const temas = (analise.temas_frequentes || []).map((t) =>
  `<li style="margin:6px 0"><b>${esc(NOMES[t.tema] || t.tema)}</b> (${esc(t.quantidade)}): ${esc(t.observacao)}</li>`).join('');
const lacunas = (analise.lacunas || []).map((l) =>
  `<div style="background:${AQ2};border:1px solid #bdeef3;border-radius:12px;padding:12px 14px;margin-top:10px">
   <div style="font-weight:700;color:#0b6e78">${esc(l.assunto)}</div>
   ${(l.exemplos || []).length ? `<div style="font-size:12px;color:${SOFT};margin:5px 0">Ex.: "${(l.exemplos || []).map(esc).join('", "')}"</div>` : ''}
   <div style="font-size:13px">${esc(l.sugestao)}</div></div>`).join('') || `<p style="font-size:13px;color:${SOFT}">Nenhuma lacuna nesta semana.</p>`;
const melhorias = (analise.melhorias || []).map((m) => `<li style="margin:6px 0">${esc(m)}</li>`).join('');

const card = (titulo, corpo) =>
  `<div style="background:#fff;border:1px solid ${LINE};border-radius:16px;padding:18px 20px;margin-top:14px">
   <div style="font-size:15px;font-weight:700;margin-bottom:10px">${titulo}</div>${corpo}</div>`;

const email_html = `<div style="background:#f7f5fb;padding:24px 0;font-family:Arial,Helvetica,sans-serif;color:${INK}">
<table align="center" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%"><tr><td style="padding:0 16px">
 <div style="border-bottom:3px solid ${AQ};padding-bottom:14px">
  <div style="font-size:12px;font-weight:700;color:${LIL};letter-spacing:.5px">ACOLHE · RELATÓRIO SEMANAL DO RH</div>
  <div style="font-size:24px;font-weight:700;color:${LIL};margin-top:4px">Dúvidas dos estagiários na semana</div>
  <div style="font-size:13px;color:${SOFT};margin-top:4px">Lumina Tecnologia (empresa fictícia) · gerado em ${hoje} pelo agente analista</div>
 </div>
 <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:12px"><tr>
  ${kpi('Perguntas', numeros.total, 'nos últimos 7 dias', LIL, '#fff')}
  ${kpi('Respondidas', pct(numeros.respondidas, numeros.total) + '%', numeros.respondidas + ' pelo manual', '#fff', INK)}
  ${kpi('Encaminhadas', numeros.encaminhadas, 'com e-mail ao RH', AQ2, INK)}
  ${kpi('Sensíveis', motivos.sensivel || 0, 'texto não incluído', '#fff', INK)}
 </tr></table>
 ${card('Resumo da semana', `<div style="border-left:4px solid ${LIL};background:${LIL2};border-radius:0 10px 10px 0;padding:12px 14px;font-size:14px;line-height:1.55">${esc(analise.resumo)}</div>`)}
 ${card('Perguntas por tema', `<table width="100%" cellpadding="0" cellspacing="0">${barras}</table>`)}
 ${card('Por que foram encaminhadas', `<table width="100%" cellpadding="0" cellspacing="0">${linhaMotivo('Fora do manual', motivos.fora_da_base)}${linhaMotivo('Assunto sensível', motivos.sensivel)}${linhaMotivo('Pedido pessoal', motivos.pedido_pessoal)}</table>`)}
 ${card('Temas em destaque', `<ul style="margin:0;padding-left:18px;font-size:13.5px;line-height:1.5">${temas}</ul>`)}
 ${card('Lacunas do manual', `<div style="font-size:12px;color:${SOFT}">Só entram perguntas que o manual não respondeu.</div>${lacunas}`)}
 ${card('Sugestões para o onboarding', `<ul style="margin:0;padding-left:18px;font-size:13.5px;line-height:1.5">${melhorias}</ul>`)}
 <p style="font-size:11px;color:${SOFT};line-height:1.5;margin-top:16px">Números calculados por código; resumo, lacunas e sugestões escritos pela IA. Perguntas sensíveis entram só na contagem: o texto delas não vai para o modelo nem para este e-mail. Enviado automaticamente pelo Acolhe.</p>
</td></tr></table></div>`;

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
            # Mapeamento fixo: só as 5 colunas (o e-mail em HTML não vai para a planilha).
            "columns": {
                "mappingMode": "defineBelow",
                "value": {c: "={{ $json." + c + " }}" for c in COLUNAS_ANALISES},
                "matchingColumns": [],
                "schema": [{"id": c, "displayName": c, "required": False, "defaultMatch": False,
                            "display": True, "type": "string", "canBeUsedToMatch": True}
                           for c in COLUNAS_ANALISES],
            },
            "options": {},
        }),
    ]

    nos.append(no("enviar_relatorio_rh", "n8n-nodes-base.gmail", 2.1, [1460, 100], {
        "sendTo": EMAIL_RH,
        "subject": "=Acolhe | Relatório semanal do RH: {{ $('interpretar_analise').item.json.total }} perguntas",
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
