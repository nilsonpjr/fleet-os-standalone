import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Search, Wrench, Clock, ChevronRight, Car } from 'lucide-react'
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

export default function RequestsPage() {
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
      r.vehicle?.model.toLowerCase().includes(needle)
    )
  }, [requests, search])

  return (
    <div className="space-y-6 animate-fadein">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Minhas Solicitações</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Acompanhe o status e aprove orçamentos de seus serviços.
          </p>
        </div>
        <button
          onClick={() => navigate('/client/requests/new')}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500 text-navy-950 font-bold hover:bg-amber-400 transition-all text-sm shadow-lg shadow-amber-500/10"
        >
          <Plus className="w-4 h-4" />
          Nova Solicitação
        </button>
      </div>

      <div className="bg-navy-800 border border-navy-700 rounded-2xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por descrição ou veículo..."
            className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-navy-900 border border-navy-700 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          />
        </div>
        
        <div className="flex gap-2 w-full md:w-auto overflow-x-auto no-scrollbar">
          {['TODAS', 'OPEN', 'QUOTED', 'IN_PROGRESS', 'DONE'].map(status => (
            <button
              key={status}
              className="px-3 py-1.5 rounded-lg border border-navy-700 text-[10px] font-bold uppercase text-slate-500 hover:text-slate-300 hover:bg-navy-700 transition-all whitespace-nowrap"
            >
              {status === 'TODAS' ? 'Todas' : status}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          <TableSkeleton rows={5} cols={4} />
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Clock className="w-10 h-10" />}
          title="Nenhuma solicitação"
          description={search ? "Nenhum resultado para sua busca." : "Você ainda não possui solicitações de serviço abertas."}
          action={
            <button
              onClick={() => navigate('/client/requests/new')}
              className="px-6 py-2 rounded-xl bg-navy-800 border border-navy-700 text-slate-300 font-bold hover:bg-navy-700 transition-all"
            >
              Abrir Primeiro Chamado
            </button>
          }
        />
      ) : (
        <div className="bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden divide-y divide-navy-700">
          {filtered.map((r) => (
            <div 
              key={r.id} 
              onClick={() => navigate(`/client/requests/${r.id}`)}
              className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-navy-700/30 transition-all cursor-pointer group"
            >
              <div className="flex gap-4">
                <div className={`w-12 h-12 rounded-xl border flex items-center justify-center shrink-0 ${
                  r.status === 'DONE' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-500' :
                  r.status === 'QUOTED' ? 'bg-amber-500/10 border-amber-500/30 text-amber-500' :
                  'bg-navy-900 border-navy-700 text-slate-500'
                }`}>
                  {r.status === 'DONE' ? <Clock className="w-6 h-6" /> : <Wrench className="w-6 h-6" />}
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-100 font-bold">Solicitação #{r.id}</span>
                    <StatusBadge status={r.status} />
                  </div>
                  <div className="text-sm text-slate-300 line-clamp-1 max-w-md">
                    {r.problemDescription}
                  </div>
                  <div className="flex items-center gap-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    <span className="flex items-center gap-1">
                      <Car className="w-3 h-3" />
                      {r.vehicle?.plate || 'Geral'}
                    </span>
                    <span>•</span>
                    <span>{fmtDate(r.createdAt)}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-between md:justify-end gap-6">
                <div className="flex flex-col items-end gap-1">
                  <div className="text-[10px] font-bold text-slate-500 uppercase">Urgência</div>
                  <UrgencyBadge urgency={r.urgency} />
                </div>
                <ChevronRight className="w-5 h-5 text-slate-600 group-hover:text-amber-500 group-hover:translate-x-1 transition-all" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
