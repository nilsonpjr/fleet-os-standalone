import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Wrench, Clock, ChevronRight, AlertCircle } from 'lucide-react'
import api from '@core/api/client'
import { useApi } from '@shared/hooks/useApi'
import { EmptyState, TableSkeleton, StatusBadge, UrgencyBadge } from '@shared/components/ui'
import { FleetRequest } from '@core/types'

function fmtDate(v?: string | null): string {
  if (!v) return '—'
  const dt = new Date(v)
  if (Number.isNaN(dt.getTime())) return v
  return dt.toLocaleDateString('pt-BR')
}

export default function WorkshopRequestsPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  
  const { data: requests = [], loading, error } = useApi<FleetRequest[]>(() => 
    api.get('/api/fleet/requests')
  )

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase()
    if (!needle) return requests
    return requests.filter((r) =>
      r.problemDescription.toLowerCase().includes(needle) ||
      r.vehicle?.plate.toLowerCase().includes(needle) ||
      r.client?.name.toLowerCase().includes(needle)
    )
  }, [requests, search])

  // Split into "Pending Quote" and "In Execution"
  const pending = filtered.filter(r => ['OPEN', 'ASSIGNED'].includes(r.status))
  const ongoing = filtered.filter(r => ['CLIENT_APPROVED', 'IN_PROGRESS'].includes(r.status))

  return (
    <div className="space-y-6 animate-fadein">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Painel da Oficina</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Gerencie orçamentos e acompanhe a execução dos serviços atribuídos.
          </p>
        </div>
      </div>

      <div className="bg-navy-800 border border-navy-700 rounded-2xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por cliente, veículo ou problema..."
            className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-navy-900 border border-navy-700 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          />
        </div>
        
        <div className="flex gap-4">
          <div className="text-center px-4 py-1 border-r border-navy-700">
            <div className="text-lg font-bold text-slate-100">{pending.length}</div>
            <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">A Orçar</div>
          </div>
          <div className="text-center px-4 py-1">
            <div className="text-lg font-bold text-blue-400">{ongoing.length}</div>
            <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Executando</div>
          </div>
        </div>
      </div>

      {error && (
        <div className="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <h2 className="text-sm font-bold text-slate-500 uppercase tracking-[0.2em] px-1">Pendentes de Orçamento</h2>
        
        {loading ? (
          <TableSkeleton rows={3} cols={4} />
        ) : pending.length === 0 ? (
          <div className="py-12 bg-navy-800/30 border border-dashed border-navy-700 rounded-2xl text-center">
            <Wrench className="w-10 h-10 text-slate-700 mx-auto mb-2" />
            <p className="text-slate-500 text-sm italic">Nenhum chamado pendente de orçamento.</p>
          </div>
        ) : (
          <div className="bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden divide-y divide-navy-700">
            {pending.map((r) => (
              <div 
                key={r.id} 
                onClick={() => navigate(`/workshop/requests/${r.id}/quote`)}
                className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-navy-700/30 transition-all cursor-pointer group"
              >
                <div className="flex gap-4">
                  <div className="w-12 h-12 rounded-xl bg-navy-900 border border-navy-700 flex items-center justify-center shrink-0 text-slate-500">
                    <Wrench className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-100 font-bold">Chamado #{r.id}</span>
                      <UrgencyBadge urgency={r.urgency} />
                    </div>
                    <div className="text-sm text-slate-300 font-medium">
                      {r.client?.name}
                    </div>
                    <div className="text-xs text-slate-500 line-clamp-1 max-w-md">
                      {r.problemDescription}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center justify-between md:justify-end gap-6">
                  <div className="text-right">
                    <div className="text-slate-100 font-plate text-sm uppercase">{r.vehicle?.plate || 'Geral'}</div>
                    <div className="text-[10px] text-slate-500 font-bold">{fmtDate(r.createdAt)}</div>
                  </div>
                  <button className="px-4 py-2 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-bold group-hover:bg-blue-500 group-hover:text-white transition-all">
                    Montar Orçamento
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-4">
        <h2 className="text-sm font-bold text-slate-500 uppercase tracking-[0.2em] px-1">Em Execução / Aprovados</h2>
        {ongoing.length > 0 && (
          <div className="bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden divide-y divide-navy-700">
            {ongoing.map((r) => (
              <div 
                key={r.id} 
                onClick={() => navigate(`/workshop/execution`)}
                className="p-5 flex items-center justify-between gap-4 hover:bg-navy-700/30 transition-all cursor-pointer"
              >
                <div className="flex gap-4">
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0 text-emerald-500">
                    <Clock className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-100 font-bold">#{r.id}</span>
                      <StatusBadge status={r.status} />
                    </div>
                    <div className="text-xs text-slate-400">{r.client?.name} • {r.vehicle?.plate}</div>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-slate-700" />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
