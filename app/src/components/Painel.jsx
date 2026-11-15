import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { buscarDados, configurado, NOMES_MOTIVOS, NOMES_TEMAS } from '../api.js'

const COR_1 = '#2a78d6'
const COR_2 = '#eb6834'
const EIXO = { fontSize: 12, fill: '#5c574f' }

export default function Painel() {
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(false)

  const carregar = useCallback(async () => {
    if (!configurado) return
    setCarregando(true)
    setErro('')
    try {
      setDados(await buscarDados())
    } catch (e) {
      setErro('Não foi possível carregar os dados agora. ' + e.message)
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregar()
  }, [carregar])

  const numeros = useMemo(() => calcular(dados?.registros || []), [dados])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <h1 className="font-display text-3xl text-floresta">Painel do RH</h1>
          <p className="text-sm text-tinta-suave">
            O que os estagiários perguntaram ao Acolhe e o que o manual ainda não cobre.
          </p>
        </div>
        <button
          onClick={carregar}
          disabled={carregando || !configurado}
          className="ml-auto rounded-full border border-linha bg-white px-4 py-2 text-sm hover:border-floresta disabled:opacity-50"
        >
          {carregando ? 'Atualizando…' : 'Atualizar'}
        </button>
      </div>

      {erro && <p className="rounded-xl bg-mel-claro px-4 py-3 text-sm">{erro}</p>}

      {dados && numeros.total === 0 && (
        <p className="rounded-2xl border border-dashed border-linha bg-white px-6 py-10 text-center text-tinta-suave">
          Ainda não há perguntas registradas. Faça uma pergunta na aba de conversa e atualize o painel.
        </p>
      )}

      {numeros.total > 0 && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Indicador rotulo="Perguntas recebidas" valor={numeros.total} />
            <Indicador
              rotulo="Respondidas pelo manual"
              valor={pct(numeros.respondidas, numeros.total)}
              detalhe={`${numeros.respondidas} de ${numeros.total}`}
            />
            <Indicador
              rotulo="Encaminhadas ao RH"
              valor={numeros.encaminhadas}
              detalhe={pct(numeros.encaminhadas, numeros.total) + ' do total'}
            />
            <Indicador
              rotulo="Assuntos sensíveis"
              valor={numeros.porMotivo.sensivel || 0}
              detalhe="texto oculto neste painel"
            />
          </div>

          <div className="grid lg:grid-cols-5 gap-4">
            <Cartao titulo="Perguntas por tema" className="lg:col-span-3">
              <ResponsiveContainer width="100%" height={Math.max(220, numeros.porTema.length * 34)}>
                <BarChart data={numeros.porTema} layout="vertical" margin={{ left: 8, right: 16 }}>
                  <CartesianGrid horizontal={false} stroke="#eee7db" />
                  <XAxis type="number" allowDecimals={false} tick={EIXO} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="nome" width={140} tick={EIXO} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: '#f1ebe0' }} content={<Dica />} />
                  <Bar isAnimationActive={false} dataKey="quantidade" name="Perguntas" fill={COR_1} radius={[0, 4, 4, 0]} barSize={18} />
                </BarChart>
              </ResponsiveContainer>
              <TabelaOculta
                colunas={['Tema', 'Perguntas']}
                linhas={numeros.porTema.map((t) => [t.nome, t.quantidade])}
              />
            </Cartao>

            <Cartao titulo="Por que foram encaminhadas" className="lg:col-span-2">
              {numeros.encaminhadas === 0 ? (
                <p className="text-sm text-tinta-suave">Nenhum encaminhamento ainda.</p>
              ) : (
                <ul className="space-y-4">
                  {Object.entries(NOMES_MOTIVOS).map(([chave, nome]) => {
                    const qtd = numeros.porMotivo[chave] || 0
                    return (
                      <li key={chave}>
                        <div className="flex justify-between text-sm">
                          <span>{nome}</span>
                          <span className="font-medium">{qtd}</span>
                        </div>
                        <div className="mt-1.5 h-2 rounded-full bg-areia">
                          <div
                            className="h-2 rounded-full"
                            style={{ width: `${(qtd / numeros.encaminhadas) * 100}%`, background: COR_2 }}
                          />
                        </div>
                      </li>
                    )
                  })}
                </ul>
              )}
              <p className="mt-6 text-xs text-tinta-suave">
                Perguntas fora do manual mostram onde ele pode melhorar. Assuntos sensíveis sempre vão para uma pessoa.
              </p>
            </Cartao>
          </div>

          <Cartao titulo="Perguntas por dia">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={numeros.porDia} margin={{ left: -16, right: 8 }}>
                <CartesianGrid vertical={false} stroke="#eee7db" />
                <XAxis dataKey="dia" tick={EIXO} axisLine={false} tickLine={false} />
                <YAxis allowDecimals={false} tick={EIXO} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: '#f1ebe0' }} content={<Dica />} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} formatter={(v) => <span style={{ color: "#5c574f" }}>{v}</span>} />
                <Bar isAnimationActive={false} dataKey="respondidas" name="Respondidas" stackId="a" fill={COR_1} stroke="#fff" strokeWidth={2} maxBarSize={40} />
                <Bar isAnimationActive={false} dataKey="encaminhadas" name="Encaminhadas" stackId="a" fill={COR_2} stroke="#fff" strokeWidth={2} radius={[4, 4, 0, 0]} maxBarSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </Cartao>

          <Analise analise={dados.analise} />

          <Cartao titulo="Últimas perguntas">
            <ul className="divide-y divide-linha">
              {numeros.recentes.map((r, i) => (
                <li key={i} className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2.5 text-sm">
                  <span className="w-24 shrink-0 text-xs text-tinta-suave">{formatarData(r.data)}</span>
                  <span className={`flex-1 min-w-[12rem] ${r.pergunta ? '' : 'italic text-tinta-suave'}`}>
                    {r.pergunta || 'Assunto sensível (conteúdo oculto)'}
                  </span>
                  <Etiqueta status={r.status} />
                </li>
              ))}
            </ul>
          </Cartao>
        </>
      )}

      {dados && (
        <p className="text-xs text-tinta-suave">
          Atualizado em {formatarData(dados.atualizado_em)}. Os dados vêm dos testes do projeto, não de uso real numa empresa.
        </p>
      )}
    </div>
  )
}

function calcular(registros) {
  const total = registros.length
  const respondidas = registros.filter((r) => r.status === 'respondida').length
  const encaminhadas = registros.filter((r) => r.status === 'encaminhada').length

  const contagemTema = {}
  const porMotivo = {}
  const dias = {}

  for (const r of registros) {
    const tema = NOMES_TEMAS[r.tema] || 'Outros'
    contagemTema[tema] = (contagemTema[tema] || 0) + 1
    if (r.motivo_encaminhamento) porMotivo[r.motivo_encaminhamento] = (porMotivo[r.motivo_encaminhamento] || 0) + 1

    const dia = r.data ? r.data.slice(0, 10) : 'sem data'
    dias[dia] ??= { respondidas: 0, encaminhadas: 0 }
    if (r.status === 'respondida') dias[dia].respondidas++
    if (r.status === 'encaminhada') dias[dia].encaminhadas++
  }

  const porTema = Object.entries(contagemTema)
    .map(([nome, quantidade]) => ({ nome, quantidade }))
    .sort((a, b) => b.quantidade - a.quantidade)

  const porDia = Object.keys(dias)
    .sort()
    .slice(-14)
    .map((d) => ({ dia: d === 'sem data' ? d : d.split('-').reverse().slice(0, 2).join('/'), ...dias[d] }))

  const recentes = [...registros].sort((a, b) => String(b.data).localeCompare(String(a.data))).slice(0, 10)

  return { total, respondidas, encaminhadas, porTema, porMotivo, porDia, recentes }
}

function Analise({ analise }) {
  if (!analise) {
    return (
      <Cartao titulo="Relatório semanal do agente analista">
        <p className="text-sm text-tinta-suave">
          O relatório ainda não foi gerado. Ele roda toda segunda às 8h, ou na mão pelo fluxo “Acolhe: agente analista” no n8n.
        </p>
      </Cartao>
    )
  }

  return (
    <Cartao
      titulo="Relatório semanal do agente analista"
      extra={<span className="text-xs text-tinta-suave">gerado em {formatarData(analise.data)}</span>}
    >
      <p className="text-sm leading-relaxed">{analise.resumo}</p>

      {analise.lacunas?.length > 0 && (
        <div className="mt-5">
          <h3 className="text-sm font-bold text-floresta">Lacunas no manual</h3>
          <ul className="mt-2 grid sm:grid-cols-2 gap-3">
            {analise.lacunas.map((l, i) => (
              <li key={i} className="rounded-xl border border-linha bg-creme p-3 text-sm">
                <p className="font-medium">{l.assunto}</p>
                {l.exemplos?.length > 0 && (
                  <p className="mt-1 text-xs text-tinta-suave">Ex.: “{l.exemplos.join('”, “')}”</p>
                )}
                <p className="mt-2">{l.sugestao}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {analise.melhorias?.length > 0 && (
        <div className="mt-5">
          <h3 className="text-sm font-bold text-floresta">Sugestões para o onboarding</h3>
          <ul className="mt-2 list-disc pl-5 space-y-1 text-sm">
            {analise.melhorias.map((m, i) => <li key={i}>{m}</li>)}
          </ul>
        </div>
      )}
    </Cartao>
  )
}

function Cartao({ titulo, extra, className = '', children }) {
  return (
    <section className={`rounded-2xl border border-linha bg-white p-5 ${className}`}>
      <div className="mb-4 flex items-baseline gap-3">
        <h2 className="font-medium">{titulo}</h2>
        {extra && <div className="ml-auto">{extra}</div>}
      </div>
      {children}
    </section>
  )
}

function Indicador({ rotulo, valor, detalhe }) {
  return (
    <div className="rounded-2xl border border-linha bg-white p-4">
      <p className="text-xs text-tinta-suave">{rotulo}</p>
      <p className="mt-1 font-display text-3xl text-tinta">{valor}</p>
      {detalhe && <p className="mt-0.5 text-xs text-tinta-suave">{detalhe}</p>}
    </div>
  )
}

function Etiqueta({ status }) {
  const estilos = {
    respondida: 'bg-[#e3eefb] text-[#1c5cab]',
    encaminhada: 'bg-[#fde6dc] text-[#9a3a12]',
  }
  const nomes = { respondida: 'Respondida', encaminhada: 'Encaminhada' }
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${estilos[status] || 'bg-areia text-tinta-suave'}`}>
      {nomes[status] || 'Erro'}
    </span>
  )
}

function Dica({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-linha bg-white px-3 py-2 text-xs shadow-sm">
      <p className="font-medium text-tinta">{label || payload[0].payload.nome}</p>
      {payload.map((p) => (
        <p key={p.dataKey} className="mt-0.5 flex items-center gap-1.5 text-tinta-suave">
          <span className="h-2 w-2 rounded-full" style={{ background: p.fill }} />
          {p.name}: <span className="font-medium text-tinta">{p.value}</span>
        </p>
      ))}
    </div>
  )
}

function TabelaOculta({ colunas, linhas }) {
  return (
    <details className="mt-3 text-sm">
      <summary className="cursor-pointer text-xs text-tinta-suave">Ver como tabela</summary>
      <table className="mt-2 w-full text-left">
        <thead>
          <tr className="text-xs text-tinta-suave">
            {colunas.map((c) => <th key={c} className="py-1 font-normal">{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {linhas.map((l, i) => (
            <tr key={i} className="border-t border-linha">
              {l.map((v, j) => <td key={j} className="py-1">{v}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  )
}

function pct(parte, total) {
  return total ? `${Math.round((parte / total) * 100)}%` : '0%'
}

function formatarData(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}
