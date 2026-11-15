import { useState } from 'react'
import Chat from './components/Chat.jsx'
import Painel from './components/Painel.jsx'
import { configurado } from './api.js'

const ABAS = [
  { id: 'chat', rotulo: 'Conversar com o Acolhe' },
  { id: 'painel', rotulo: 'Painel do RH' },
]

export default function App() {
  const [aba, setAba] = useState('chat')

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-linha bg-creme/90 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 py-3 flex flex-wrap items-center gap-x-6 gap-y-3">
          <div className="flex items-center gap-3">
            <img src="/favicon.svg" alt="" className="h-9 w-9" />
            <div className="leading-tight">
              <p className="font-display text-xl text-floresta">Acolhe</p>
              <p className="text-xs text-tinta-suave">Onboarding de estagiários · Lumina Tecnologia</p>
            </div>
          </div>

          <nav className="ml-auto flex rounded-full bg-areia p-1" aria-label="Seções">
            {ABAS.map((item) => (
              <button
                key={item.id}
                onClick={() => setAba(item.id)}
                aria-current={aba === item.id ? 'page' : undefined}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
                  aba === item.id
                    ? 'bg-floresta text-creme shadow-sm'
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
        <div className="mx-auto max-w-5xl w-full px-4 sm:px-6 pt-4">
          <p className="rounded-xl border border-mel bg-mel-claro px-4 py-3 text-sm">
            Falta configurar o endereço do n8n. Crie o arquivo <code>.env</code> com{' '}
            <code>VITE_N8N_WEBHOOK_BASE</code> (veja o <code>.env.example</code>).
          </p>
        </div>
      )}

      <main className="flex-1 mx-auto w-full max-w-5xl px-4 sm:px-6 py-6">
        {aba === 'chat' ? <Chat /> : <Painel />}
      </main>

      <footer className="border-t border-linha">
        <p className="mx-auto max-w-5xl px-4 sm:px-6 py-4 text-xs text-tinta-suave">
          Projeto de portfólio de Anna Julia. A Lumina Tecnologia e o manual são fictícios.
          As respostas são geradas por IA a partir do manual e podem conter erros.
        </p>
      </footer>
    </div>
  )
}
