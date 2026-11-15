// Comunicação com os webhooks do n8n.
// A chave do Gemini nunca passa por aqui: ela fica guardada no n8n.

const BASE = (import.meta.env.VITE_N8N_WEBHOOK_BASE || '').replace(/\/$/, '')

export const configurado = Boolean(BASE)

export async function perguntar(pergunta) {
  const resposta = await fetch(`${BASE}/acolhe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pergunta }),
  })
  if (!resposta.ok) throw new Error(`O servidor respondeu ${resposta.status}`)

  const dados = await resposta.json()
  return {
    ...dados,
    fontes: String(dados.fontes || '')
      .split(';')
      .map((f) => f.trim())
      .filter(Boolean),
  }
}

export async function buscarDados() {
  const resposta = await fetch(`${BASE}/acolhe-dados`)
  if (!resposta.ok) throw new Error(`O servidor respondeu ${resposta.status}`)
  return resposta.json()
}

export const NOMES_TEMAS = {
  admissao: 'Admissão',
  primeira_semana: 'Primeira semana',
  jornada_ponto: 'Jornada e ponto',
  provas: 'Provas',
  bolsa: 'Bolsa',
  transporte: 'Transporte',
  beneficios: 'Benefícios',
  recesso: 'Recesso',
  faltas_atestados: 'Faltas e atestados',
  hibrido_equipamento: 'Híbrido e equipamento',
  acessos_ti: 'Acessos e TI',
  avaliacao: 'Avaliação',
  efetivacao: 'Efetivação',
  conduta: 'Conduta',
  etica_sensivel: 'Ética e sensíveis',
  desligamento: 'Fim do estágio',
  outros: 'Outros',
}

export const NOMES_MOTIVOS = {
  fora_da_base: 'Fora do manual',
  sensivel: 'Assunto sensível',
  pedido_pessoal: 'Pedido pessoal',
}
