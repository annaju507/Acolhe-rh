import { useState } from 'react'
import Chat from './components/Chat.jsx'
import Painel from './components/Painel.jsx'
import { configurado } from './api.js'

const ABAS = [
  { id: 'chat', rotulo: 'Conversar' },
  { id: 'painel', rotulo: 'Painel do RH' },
]

export default function App() {
  const [aba, setAba] = useState('chat')

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-10 bg-fundo/70 backdrop-blur">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 py-4 flex flex-wrap items-center gap-x-6 gap-y-3">
          <div className="flex items-center gap-2.5 rounded-full bg-white py-1.5 pl-1.5 pr-4 shadow-sm">
            <img src="/avatar-acolhe.png" alt="" className="h-8 w-8 rounded-full" />
            <div className="leading-tight">
              <p className="text-sm font-semibold">Acolhe</p>
              <p className="text-[11px] text-tinta-suave">Lumina Tecnologia</p>
            </div>
          </div>

          <nav className="ml-auto flex rounded-full bg-white p-1 shadow-sm" aria-label="Seções">
            {ABAS.map((item) => (
              <button
                key={item.id}
                onClick={() => setAba(item.id)}
                aria-current={aba === item.id ? 'page' : undefined}
                className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                  aba === item.id
                    ? 'bg-grafite text-white'
                    : 'text-tinta-suave hover:text-tinta'
                }`}
              >
                {item.rotulo}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {!configurado && (
        <div className="mx-auto max-w-5xl w-full px-4 sm:px-6 pt-2">
          <p className="rounded-2xl bg-manteiga px-4 py-3 text-sm">
            Falta configurar o endereço do n8n. Crie o arquivo <code>.env</code> com{' '}
            <code>VITE_N8N_WEBHOOK_BASE</code> (veja o <code>.env.example</code>).
          </p>
        </div>
      )}

      <main className="flex-1 mx-auto w-full max-w-5xl px-4 sm:px-6 py-6">
        {aba === 'chat' ? <Chat /> : <Painel />}
      </main>

      <footer>
        <p className="mx-auto max-w-5xl px-4 sm:px-6 py-5 text-xs text-tinta-suave">
          Projeto de portfólio de Anna Julia. A Lumina Tecnologia e o manual são fictícios.
          As respostas são geradas por IA a partir do manual e podem conter erros.
        </p>
      </footer>
    </div>
  )
}
