import { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, ClipboardList, RefreshCw, Search, Send, TriangleAlert, Clock } from 'lucide-react'
import api from '@core/api/client'
import { EmptyState, StatusBadge, TableSkeleton, UrgencyBadge } from '@shared/components/ui'
import ChatWidget from '@shared/components/ChatWidget'

type RequestStatus =
  | 'OPEN'
  | 'ASSIGNED'
  | 'QUOTED'
  | 'ADMIN_APPROVED'
  | 'CLIENT_APPROVED'
  | 'REVISION_REQUESTED'
  | 'IN_PROGRESS'
  | 'AWAITING_CLOSURE'
  | 'DONE'
  | 'CANCELED'

interface FleetRequest {
  id: number
  client_id: number
  vehicle_id?: number | null
  boat_id?: number | null
  problem_description: string
  urgency: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  status: RequestStatus
  assigned_workshop_ids: number[]
  created_at: string
  updated_at: string
}

interface Workshop {
  id: number
  name: string
  city?: string | null
  state?: string | null
}

interface QuoteItem {
  id: number
  type: 'PART' | 'LABOR' | 'OTHER'
  description: string
  quantity: number
  unit_price: number
  total: number
}

interface Quote {
  id: number
  workshop_id: number
  technician_name?: string | null
  diagnosis?: string | null
  estimated_days?: number | null
  validity_days?: number | null
  subtotal_parts: number
  subtotal_labor: number
  total_value: number
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'REVISION_REQUESTED'
  revision_notes?: string | null
  created_at: string
  submitted_at?: string | null
  items: QuoteItem[]
}

const STATUS_FILTERS: Array<{ id: 'ALL' | RequestStatus; label: string }> = [
  { id: 'ALL', label: 'Todos' },
  { id: 'OPEN', label: 'Abertas' },
  { id: 'ASSIGNED', label: 'Encaminhadas' },
  { id: 'QUOTED', label: 'Orçadas' },
  { id: 'IN_PROGRESS', label: 'Execução' },
  { id: 'DONE', label: 'Concluídas' },
]

function fmtDate(v: string): string {
  const dt = new Date(v)
  if (Number.isNaN(dt.getTime())) return v
  return dt.toLocaleDateString('pt-BR')
}

function fmtMoney(v: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0)
}

export default function RequestsPage() {
  const [requests, setRequests] = useState<FleetRequest[]>([])
  const [workshops, setWorkshops] = useState<Workshop[]>([])
  const [quotes, setQuotes] = useState<Quote[]>([])
  const [selectedRequestId, setSelectedRequestId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'ALL' | RequestStatus>('ALL')
  const [selectedWorkshopIds, setSelectedWorkshopIds] = useState<number[]>([])
  const [revisionNotes, setRevisionNotes] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(true)
  const [loadingQuotes, setLoadingQuotes] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadBase = async () => {
    setLoading(true)
    setError(null)
    try {
      const [reqs, ws] = await Promise.all([
        api.get<FleetRequest[]>('/api/fleet/requests'),
        api.get<Workshop[]>('/api/fleet/workshops'),
      ])
      setRequests(reqs)
      setWorkshops(ws)
      if (!selectedRequestId && reqs.length > 0) {
        setSelectedRequestId(reqs[0].id)
      }
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Falha ao carregar solicitações')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadBase()
  }, [])

  const selectedRequest = useMemo(
    () => requests.find((r) => r.id === selectedRequestId) ?? null,
    [requests, selectedRequestId]
  )

  useEffect(() => {
    const loadQuotes = async () => {
      if (!selectedRequestId) {
        setQuotes([])
        return
      }
      setLoadingQuotes(true)
      try {
        const data = await api.get<Quote[]>(`/api/fleet/requests/${selectedRequestId}/quotes`)
        setQuotes(data)
      } catch (err) {
        setQuotes([])
        setError(typeof err === 'string' ? err : 'Falha ao carregar orçamentos')
      } finally {
        setLoadingQuotes(false)
      }
    }
    loadQuotes()
  }, [selectedRequestId])

  useEffect(() => {
    if (selectedRequest) {
      setSelectedWorkshopIds(selectedRequest.assigned_workshop_ids ?? [])
    } else {
      setSelectedWorkshopIds([])
    }
  }, [selectedRequest])

  const filteredRequests = useMemo(() => {
    const needle = search.trim().toLowerCase()
    return requests.filter((r) => {
      if (statusFilter !== 'ALL' && r.status !== statusFilter) return false
      if (!needle) return true
      return (
        String(r.id).includes(needle) ||
        (r.problem_description || '').toLowerCase().includes(needle)
      )
    })
  }, [requests, search, statusFilter])

  const toggleWorkshop = (workshopId: number) => {
    setSelectedWorkshopIds((prev) =>
      prev.includes(workshopId) ? prev.filter((id) => id !== workshopId) : [...prev, workshopId]
    )
  }

  const assignWorkshops = async () => {
    if (!selectedRequest || selectedWorkshopIds.length === 0) return
    setSaving(true)
    setError(null)
    try {
      await api.post(`/api/fleet/requests/${selectedRequest.id}/assign`, { workshop_ids: selectedWorkshopIds })
      await loadBase()
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Falha ao encaminhar solicitação')
    } finally {
      setSaving(false)
    }
  }

  const approveAdmin = async (quoteId: number) => {
    if (!selectedRequest) return
    setSaving(true)
    setError(null)
    try {
      await api.post(`/api/fleet/requests/${selectedRequest.id}/approve/admin?quote_id=${quoteId}`)
      await loadBase()
      const data = await api.get<Quote[]>(`/api/fleet/requests/${selectedRequest.id}/quotes`)
      setQuotes(data)
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Falha ao aprovar orçamento')
    } finally {
      setSaving(false)
    }
  }

  const requestRevision = async (quoteId: number) => {
    if (!selectedRequest) return
    const notes = revisionNotes[quoteId]?.trim()
    if (!notes) {
      setError('Digite um motivo para solicitar revisão.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const params = new URLSearchParams({
        quote_id: String(quoteId),
        notes,
      })
      await api.post(`/api/fleet/requests/${selectedRequest.id}/revision?${params.toString()}`)
      await loadBase()
      const data = await api.get<Quote[]>(`/api/fleet/requests/${selectedRequest.id}/quotes`)
      setQuotes(data)
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Falha ao solicitar revisão')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-5 animate-fadein">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Solicitações de Frota</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Encaminhamento para oficinas e decisão de orçamentos.
          </p>
        </div>
        <button
          onClick={loadBase}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-navy-700 text-slate-300 hover:bg-navy-800 transition-all text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Atualizar
        </button>
      </div>

      {error && (
        <div className="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        <section className="xl:col-span-2 bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden">
          <div className="p-4 border-b border-navy-700 space-y-3">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar por ID ou problema"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-navy-900 border border-navy-700 text-sm text-slate-200"
              />
            </div>
            <div className="flex flex-wrap gap-1.5">
              {STATUS_FILTERS.map((f) => (
                <button
                  key={f.id}
                  onClick={() => setStatusFilter(f.id)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-bold border ${
                    statusFilter === f.id
                      ? 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                      : 'bg-navy-900 border-navy-700 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <TableSkeleton rows={7} cols={3} />
          ) : filteredRequests.length === 0 ? (
            <EmptyState
              icon={<ClipboardList className="w-7 h-7" />}
              title="Nenhuma solicitação"
              description="Quando clientes abrirem solicitações, elas aparecerão aqui."
            />
          ) : (
            <div className="divide-y divide-navy-700 max-h-[65vh] overflow-y-auto">
              {filteredRequests.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setSelectedRequestId(r.id)}
                  className={`w-full text-left px-4 py-3 transition-colors ${
                    selectedRequestId === r.id ? 'bg-amber-500/10' : 'hover:bg-navy-700/40'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-slate-500">Solicitação #{r.id} • Cliente #{r.client_id}</div>
                      <p className="text-sm text-slate-200 font-medium truncate mt-0.5">{r.problem_description}</p>
                      <p className="text-xs text-slate-500 mt-1 flex items-center gap-2">
                        Criada em {fmtDate(r.created_at)}
                        {r.status === 'ASSIGNED' && (
                          <span className={`flex items-center gap-1 ${
                            (new Date().getTime() - new Date(r.updated_at).getTime()) > 172800000 
                              ? 'text-red-400 font-bold' 
                              : 'text-slate-500'
                          }`}>
                            <Clock className="w-3 h-3" />
                            {Math.round((new Date().getTime() - new Date(r.updated_at).getTime()) / 3600000)}h aguardando
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <StatusBadge status={r.status} />
                      <UrgencyBadge urgency={r.urgency} />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="xl:col-span-3 bg-navy-800 border border-navy-700 rounded-2xl p-4 space-y-4">
          {!selectedRequest ? (
            <EmptyState
              icon={<ClipboardList className="w-7 h-7" />}
              title="Selecione uma solicitação"
              description="Escolha uma solicitação na lista para gerenciar oficinas e orçamentos."
            />
          ) : (
            <>
              <div className="border border-navy-700 rounded-2xl p-4 bg-navy-900/40">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                  <div>
                    <h2 className="text-slate-100 font-semibold">Solicitação #{selectedRequest.id}</h2>
                    <p className="text-sm text-slate-300 mt-1">{selectedRequest.problem_description}</p>
                    <p className="text-xs text-slate-500 mt-2">
                      Cliente #{selectedRequest.client_id} • Veículo #{selectedRequest.vehicle_id ?? '—'} • Embarcação #{selectedRequest.boat_id ?? '—'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={selectedRequest.status} />
                    <UrgencyBadge urgency={selectedRequest.urgency} />
                  </div>
                </div>
              </div>

              <div className="border border-navy-700 rounded-2xl p-4">
                <h3 className="text-sm font-bold text-slate-200 mb-3">Encaminhar para oficina(s)</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
                  {workshops.map((w) => (
                    <label
                      key={w.id}
                      className={`flex items-start gap-2 p-2.5 rounded-xl border cursor-pointer ${
                        selectedWorkshopIds.includes(w.id)
                          ? 'border-amber-500/40 bg-amber-500/10'
                          : 'border-navy-700 bg-navy-900/50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedWorkshopIds.includes(w.id)}
                        onChange={() => toggleWorkshop(w.id)}
                        className="mt-0.5"
                      />
                      <div>
                        <div className="text-sm text-slate-200 font-medium">{w.name}</div>
                        <div className="text-xs text-slate-500">
                          {w.city ?? '—'}{w.state ? `/${w.state}` : ''}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
                <button
                  onClick={assignWorkshops}
                  disabled={saving || selectedWorkshopIds.length === 0}
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-blue-500 text-white text-sm font-semibold disabled:opacity-60"
                >
                  <Send className="w-4 h-4" />
                  {saving ? 'Salvando...' : 'Encaminhar Solicitação'}
                </button>
              </div>

              <div className="border border-navy-700 rounded-2xl p-4">
                <h3 className="text-sm font-bold text-slate-200 mb-3">Orçamentos Recebidos</h3>
                {loadingQuotes ? (
                  <TableSkeleton rows={3} cols={4} />
                ) : quotes.length === 0 ? (
                  <EmptyState
                    icon={<TriangleAlert className="w-7 h-7" />}
                    title="Sem orçamento ainda"
                    description="As oficinas atribuídas ainda não enviaram orçamento."
                  />
                ) : (
                  <div className="space-y-3">
                    {quotes.map((q) => (
                      <article key={q.id} className="rounded-xl border border-navy-700 bg-navy-900/40 p-3.5">
                        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-2">
                          <div>
                            <p className="text-sm text-slate-200 font-semibold">
                              Orçamento #{q.id} • Oficina #{q.workshop_id}
                            </p>
                            <p className="text-xs text-slate-500 mt-0.5">
                              {q.technician_name || 'Técnico não informado'} • Enviado em {q.submitted_at ? fmtDate(q.submitted_at) : 'rascunho'}
                            </p>
                          </div>
                          <div className="text-right">
                            <StatusBadge status={q.status} map={{
                              DRAFT: 'status-open',
                              SUBMITTED: 'status-quoted',
                              APPROVED: 'status-approved',
                              REJECTED: 'status-canceled',
                              REVISION_REQUESTED: 'status-revision',
                            }} />
                            <p className="text-emerald-400 font-bold mt-1">{fmtMoney(q.total_value)}</p>
                          </div>
                        </div>

                        <p className="text-xs text-slate-300 mt-2">{q.diagnosis || 'Sem diagnóstico informado.'}</p>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3 text-xs">
                          <div className="px-2 py-1.5 rounded bg-navy-800 border border-navy-700 text-slate-300">
                            Peças: <strong>{fmtMoney(q.subtotal_parts)}</strong>
                          </div>
                          <div className="px-2 py-1.5 rounded bg-navy-800 border border-navy-700 text-slate-300">
                            Mão de obra: <strong>{fmtMoney(q.subtotal_labor)}</strong>
                          </div>
                          <div className="px-2 py-1.5 rounded bg-navy-800 border border-navy-700 text-slate-300">
                            Itens: <strong>{q.items?.length ?? 0}</strong>
                          </div>
                          <div className="px-2 py-1.5 rounded bg-navy-800 border border-navy-700 text-slate-300">
                            Prazo: <strong>{q.estimated_days ?? '—'} dia(s)</strong>
                          </div>
                        </div>

                        <div className="flex flex-col md:flex-row gap-2 mt-3">
                          <button
                            onClick={() => approveAdmin(q.id)}
                            disabled={saving}
                            className="inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold"
                          >
                            <CheckCircle2 className="w-4 h-4" />
                            Aprovar (Admin)
                          </button>
                          <input
                            value={revisionNotes[q.id] ?? ''}
                            onChange={(e) => setRevisionNotes((prev) => ({ ...prev, [q.id]: e.target.value }))}
                            placeholder="Motivo da revisão"
                            className="flex-1 px-3 py-2 rounded-lg bg-navy-800 border border-navy-700 text-xs text-slate-200"
                          />
                          <button
                            onClick={() => requestRevision(q.id)}
                            disabled={saving}
                            className="inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-orange-500/20 text-orange-300 border border-orange-500/30 text-xs font-semibold"
                          >
                            Solicitar Revisão
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </div>

              <div className="border border-navy-700 rounded-2xl p-4">
                <h3 className="text-sm font-bold text-slate-200 mb-3">Comunicação Interna</h3>
                <ChatWidget requestId={selectedRequest.id} />
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  )
}
