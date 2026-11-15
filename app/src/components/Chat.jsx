import { useEffect, useRef, useState } from 'react'
import { perguntar, configurado } from '../api.js'

const SUGESTOES = [
  'Quanto é a bolsa e quando cai?',
  'Estagiário tem férias?',
  'esqueci de bater o ponto ontem e agora?',
  'Tem estacionamento no escritório?',
]

const BOAS_VINDAS = {
  autor: 'acolhe',
  resposta:
    'Oi! Eu sou o Acolhe e respondo dúvidas sobre o seu estágio com base no Manual do Estagiário Lumina. Sempre mostro de qual seção veio a resposta. Se eu não souber, ou se o assunto for delicado, chamo uma pessoa do RH.',
  fontes: [],
}

export default function Chat() {
  const [mensagens, setMensagens] = useState([BOAS_VINDAS])
  const [texto, setTexto] = useState('')
  const [carregando, setCarregando] = useState(false)
  const fimRef = useRef(null)

  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [mensagens, carregando])

  async function enviar(pergunta) {
    const limpa = pergunta.trim()
    if (!limpa || carregando) return

    setMensagens((atual) => [...atual, { autor: 'pessoa', texto: limpa }])
    setTexto('')
    setCarregando(true)

    try {
      const dados = await perguntar(limpa)
      setMensagens((atual) => [...atual, { autor: 'acolhe', ...dados }])
    } catch {
      setMensagens((atual) => [
        ...atual,
        {
          autor: 'acolhe',
          status: 'erro',
          resposta: 'Não consegui me conectar agora. Tente de novo em alguns segundos ou escreva para rh@lumina.exemplo.',
          fontes: [],
        },
      ])
    } finally {
      setCarregando(false)
    }
  }

  const soBoasVindas = mensagens.length === 1

  return (
    <section className="mx-auto flex max-w-3xl flex-col rounded-3xl border border-linha bg-white shadow-sm h-[calc(100vh-13rem)] min-h-[480px]">
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-4" aria-live="polite">
        {mensagens.map((m, i) =>
          m.autor === 'pessoa' ? <BalaoPessoa key={i} texto={m.texto} /> : <BalaoAcolhe key={i} {...m} />,
        )}

        {soBoasVindas && (
          <div className="flex flex-wrap gap-2 pl-11">
            {SUGESTOES.map((s) => (
              <button
                key={s}
                onClick={() => enviar(s)}
                disabled={!configurado}
                className="rounded-full border border-linha bg-creme px-3 py-1.5 text-sm text-tinta-suave hover:border-floresta hover:text-floresta disabled:opacity-50 transition"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {carregando && (
          <div className="flex items-center gap-3">
            <Avatar />
            <div className="flex gap-1 rounded-2xl rounded-tl-sm bg-areia px-4 py-3" aria-label="O Acolhe está consultando o manual">
              <span className="ponto h-2 w-2 rounded-full bg-floresta" />
              <span className="ponto h-2 w-2 rounded-full bg-floresta" />
              <span className="ponto h-2 w-2 rounded-full bg-floresta" />
            </div>
            <span className="text-xs text-tinta-suave">consultando o manual…</span>
          </div>
        )}
        <div ref={fimRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          enviar(texto)
        }}
        className="border-t border-linha p-3 sm:p-4 flex gap-2"
      >
        <label htmlFor="pergunta" className="sr-only">Sua dúvida</label>
        <input
          id="pergunta"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Escreva sua dúvida sobre o estágio"
          maxLength={500}
          disabled={!configurado}
          className="flex-1 rounded-full border border-linha bg-creme px-4 py-2.5 text-sm outline-none focus:border-floresta focus:ring-2 focus:ring-floresta/20"
        />
        <button
          type="submit"
          disabled={!texto.trim() || carregando || !configurado}
          className="rounded-full bg-floresta px-5 py-2.5 text-sm font-medium text-creme hover:bg-floresta-escura disabled:opacity-40 transition"
        >
          Enviar
        </button>
      </form>
    </section>
  )
}

function Avatar() {
  return <img src="/favicon.svg" alt="" className="h-8 w-8 shrink-0 self-start" />
}

function BalaoPessoa({ texto }) {
  return (
    <div className="flex justify-end">
      <p className="max-w-[80%] rounded-2xl rounded-tr-sm bg-floresta px-4 py-2.5 text-sm text-creme whitespace-pre-wrap">
        {texto}
      </p>
    </div>
  )
}

function BalaoAcolhe({ resposta, fontes = [], status }) {
  return (
    <div className="flex gap-3">
      <Avatar />
      <div className="max-w-[85%] space-y-2">
        <div className="rounded-2xl rounded-tl-sm bg-areia px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap">
          {resposta}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {fontes.map((f) => (
            <span key={f} className="rounded-full border border-linha bg-white px-2.5 py-0.5 text-xs text-tinta-suave">
              Fonte: {f}
            </span>
          ))}
          {status === 'encaminhada' && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-mel-claro px-2.5 py-0.5 text-xs font-medium text-tinta">
              <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" aria-hidden="true">
                <path d="M2 4h12v8H2z M2 4l6 5 6-5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
              </svg>
              Encaminhado para uma pessoa do RH
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
