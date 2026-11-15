import { useEffect, useRef, useState } from 'react'
import { perguntar, configurado } from '../api.js'

const SUGESTOES = [
  { texto: 'Quanto é a bolsa e quando cai?', icone: 'carteira', estilo: 'bg-roxo text-tinta' },
  { texto: 'Estagiário tem férias?', icone: 'sol', estilo: 'bg-menta text-tinta' },
  { texto: 'esqueci de bater o ponto ontem e agora?', icone: 'relogio', estilo: 'bg-grafite text-white' },
  { texto: 'Tem estacionamento no escritório?', icone: 'pino', estilo: 'bg-white text-tinta' },
]

const INTRODUCAO =
  'Oi! Sou o Acolhe e tiro suas dúvidas sobre o estágio com base no manual da Lumina. Se eu não souber, chamo alguém do RH.'

const ERRO = 'Não consegui me conectar agora. Tente de novo em alguns segundos ou escreva para rh@lumina.exemplo.'

export default function Chat() {
  const [mensagens, setMensagens] = useState([])
  const [texto, setTexto] = useState('')
  const [carregando, setCarregando] = useState(false)
  const fimRef = useRef(null)

  useEffect(() => {
    if (mensagens.length) fimRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [mensagens, carregando])

  async function enviar(pergunta) {
    const limpa = pergunta.trim()
    if (!limpa || carregando) return

    setMensagens((atual) => [...atual, { autor: 'pessoa', texto: limpa, hora: agora() }])
    setTexto('')
    setCarregando(true)

    try {
      const dados = await perguntar(limpa)
      setMensagens((atual) => [...atual, { autor: 'acolhe', ...dados }])
    } catch {
      setMensagens((atual) => [...atual, { autor: 'acolhe', status: 'erro', resposta: ERRO, fontes: [] }])
    } finally {
      setCarregando(false)
    }
  }

  const vazio = mensagens.length === 0

  return (
    <section className="mx-auto flex max-w-3xl flex-col overflow-hidden rounded-[2rem] border border-white bg-nevoa shadow-sm h-[calc(100vh-13rem)] min-h-[520px]">
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6" aria-live="polite">
        {vazio ? (
          <BoasVindas onEscolher={enviar} />
        ) : (
          <div className="space-y-5">
            <p className="mx-auto w-fit rounded-full bg-white px-4 py-1.5 text-xs font-medium shadow-sm">Hoje</p>
            {mensagens.map((m, i) =>
              m.autor === 'pessoa' ? <BalaoPessoa key={i} {...m} /> : <BalaoAcolhe key={i} {...m} />,
            )}
            {carregando && <Digitando />}
          </div>
        )}
        <div ref={fimRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          enviar(texto)
        }}
        className="p-3 sm:p-4"
      >
        <div className="flex items-center gap-2 rounded-full bg-white p-1.5 pl-5 shadow-sm focus-within:ring-2 focus-within:ring-lavanda-forte/30">
          <label htmlFor="pergunta" className="sr-only">Sua dúvida</label>
          <input
            id="pergunta"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Escreva sua dúvida sobre o estágio…"
            maxLength={500}
            disabled={!configurado}
            className="flex-1 min-w-0 bg-transparent py-2 text-sm outline-none placeholder:text-tinta-suave disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            aria-label="Enviar"
            disabled={!texto.trim() || carregando || !configurado}
            className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-lavanda text-tinta hover:bg-lavanda-forte hover:text-white disabled:opacity-40 disabled:hover:bg-lavanda disabled:hover:text-tinta transition"
          >
            <svg viewBox="0 0 20 20" className="h-5 w-5" aria-hidden="true">
              <path d="M10 16V4M4.5 9.5 10 4l5.5 5.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </form>
    </section>
  )
}

function BoasVindas({ onEscolher }) {
  return (
    <div className="space-y-3">
      <BalaoAcolhe resposta={INTRODUCAO} />
      <div className="flex flex-wrap gap-2 pl-8">
        {SUGESTOES.map((s) => (
          <button
            key={s.texto}
            onClick={() => onEscolher(s.texto)}
            disabled={!configurado}
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm shadow-sm transition hover:-translate-y-0.5 hover:shadow disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 ${s.estilo}`}
          >
            <Icone nome={s.icone} />
            {s.texto}
          </button>
        ))}
      </div>
    </div>
  )
}

function Icone({ nome }) {
  const p = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round', strokeLinejoin: 'round' }
  const formas = {
    carteira: <><rect x="3" y="6" width="14" height="10" rx="2.5" {...p} /><path d="M3 9h14M13 12.5h1.5" {...p} /></>,
    sol: <><circle cx="10" cy="10" r="3.2" {...p} /><path d="M10 2.5v1.8M10 15.7v1.8M2.5 10h1.8M15.7 10h1.8M4.7 4.7l1.3 1.3M14 14l1.3 1.3M4.7 15.3 6 14M14 6l1.3-1.3" {...p} /></>,
    relogio: <><circle cx="10" cy="10" r="7" {...p} /><path d="M10 6v4l2.5 2" {...p} /></>,
    pino: <><path d="M10 17s5-4.6 5-8.5a5 5 0 0 0-10 0C5 12.4 10 17 10 17z" {...p} /><circle cx="10" cy="8.5" r="1.8" {...p} /></>,
  }
  return <svg viewBox="0 0 20 20" className="h-4 w-4 shrink-0" aria-hidden="true">{formas[nome]}</svg>
}

function Avatar() {
  return <img src="/avatar-acolhe.png" alt="" className="h-6 w-6 shrink-0 rounded-lg" />
}

function BalaoPessoa({ texto, hora }) {
  return (
    <div className="flex flex-col items-end gap-1.5">
      <span className="text-xs font-medium text-tinta-suave">Você</span>
      <p className="max-w-[80%] rounded-3xl rounded-tr-md bg-lavanda px-4 py-3 text-sm whitespace-pre-wrap">{texto}</p>
      {hora && <span className="text-[11px] text-tinta-suave">{hora}</span>}
    </div>
  )
}

function BalaoAcolhe({ resposta, fontes = [], status }) {
  return (
    <div className="flex flex-col items-start gap-1.5">
      <span className="flex items-center gap-2 text-xs font-medium text-tinta-suave">
        <Avatar /> Acolhe
      </span>
      <div className="max-w-[85%] space-y-2">
        <div className={`rounded-3xl rounded-tl-md px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap shadow-sm ${status === 'erro' ? 'bg-manteiga-clara' : 'bg-white'}`}>
          {resposta}
        </div>

        {(fontes.length > 0 || status === 'encaminhada') && (
          <div className="flex flex-wrap items-center gap-2">
            {fontes.map((f) => (
              <span key={f} className="rounded-full bg-lavanda-clara px-3 py-1 text-xs">
                Fonte: {f}
              </span>
            ))}
            {status === 'encaminhada' && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-manteiga px-3 py-1 text-xs font-medium">
                <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" aria-hidden="true">
                  <path d="M2 4h12v8H2z M2 4l6 5 6-5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
                </svg>
                Encaminhado para uma pessoa do RH
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function Digitando() {
  return (
    <div className="flex flex-col items-start gap-1.5">
      <span className="flex items-center gap-2 text-xs font-medium text-tinta-suave">
        <Avatar /> Acolhe
      </span>
      <div className="flex items-center gap-3">
        <div className="flex gap-1 rounded-3xl rounded-tl-md bg-white px-4 py-3.5 shadow-sm" aria-label="O Acolhe está consultando o manual">
          <span className="ponto h-2 w-2 rounded-full bg-lavanda-forte" />
          <span className="ponto h-2 w-2 rounded-full bg-lavanda-forte" />
          <span className="ponto h-2 w-2 rounded-full bg-lavanda-forte" />
        </div>
        <span className="text-xs text-tinta-suave">consultando o manual…</span>
      </div>
    </div>
  )
}

function agora() {
  return new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}
