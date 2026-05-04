import { useState, useMemo } from 'react'
import { ClipboardList, Search, ChevronDown, ChevronUp, Package, Wrench, Calendar, DollarSign } from 'lucide-react'
import { useApi } from '@shared/hooks/useApi'
import api from '@core/api/client'
import { StatusBadge, TableSkeleton } from '@shared/components/ui'

interface AssetHistoryTabProps {
  vehicleId?: number
  boatId?: number
}

export default function AssetHistoryTab({ vehicleId, boatId }: AssetHistoryTabProps) {
  const [search, setSearch] = useState('')
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const { data: history = [], loading } = useApi<any[]>(() => 
    api.get('/api/fleet/requests', { 
      vehicle_id: vehicleId, 
      boat_id: boatId,
      status: 'DONE' // Only finished ones for history
    })
  )

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase()
    if (!needle) return history
    return history.filter(r => 
      r.problem_description.toLowerCase().includes(needle) ||
      r.quotes?.some((q: any) => 
        q.items?.some((i: any) => i.description.toLowerCase().includes(needle))
      )
    )
  }, [history, search])

  if (loading) return <TableSkeleton rows={3} />

  if (history.length === 0) {
    return (
      <div className="py-12 text-center bg-navy-900/30 rounded-2xl border-2 border-dashed border-navy-700">
        <ClipboardList className="w-10 h-10 text-slate-700 mx-auto mb-3" />
        <p className="text-slate-500 text-sm">Nenhum histórico de manutenção disponível para este ativo.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search History */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar no histórico (ex: óleo, correia, freio)..."
          className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500/40"
        />
      </div>

      <div className="space-y-3">
        {filtered.map((request) => {
          const isExpanded = expandedId === request.id
          const approvedQuote = (request.quotes || []).find((q: any) => q.status === 'APPROVED' || q.status === 'DONE')
          
          return (
            <div 
              key={request.id} 
              className={`bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden transition-all ${isExpanded ? 'ring-1 ring-sky-500/30' : ''}`}
            >
              <div 
                onClick={() => setExpandedId(isExpanded ? null : request.id)}
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-navy-700/30 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-navy-900 border border-navy-700 flex items-center justify-center text-slate-500">
                    <Calendar className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-slate-200">
                      {new Date(request.created_at).toLocaleDateString('pt-BR')}
                    </div>
                    <div className="text-xs text-slate-400 line-clamp-1 max-w-md">
                      {request.problem_description}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-4">
                  <div className="text-right hidden sm:block">
                    <div className="text-sm font-bold text-slate-100">
                      {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(approvedQuote?.total_value || 0)}
                    </div>
                    <div className="text-[10px] font-bold text-slate-600 uppercase">Valor Total</div>
                  </div>
                  {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                </div>
              </div>

              {isExpanded && (
                <div className="px-4 pb-4 animate-slideDown">
                  <div className="pt-4 border-t border-navy-700 space-y-4">
                    {/* Diagnosis Summary */}
                    <div>
                      <h4 className="text-[10px] font-bold text-sky-400 uppercase tracking-widest mb-2">Diagnóstico da Oficina</h4>
                      <p className="text-sm text-slate-300 bg-navy-900/50 p-3 rounded-xl border border-navy-700 italic">
                        "{approvedQuote?.diagnosis || 'Sem diagnóstico registrado.'}"
                      </p>
                    </div>

                    {/* Items List */}
                    <div>
                      <h4 className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest mb-2">Itens Utilizados</h4>
                      <div className="space-y-1.5">
                        {approvedQuote?.items?.map((item: any, idx: number) => (
                          <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl bg-navy-900/30 border border-navy-700/50 text-xs">
                            <div className="flex items-center gap-2">
                              {item.type === 'PART' ? <Package className="w-3 h-3 text-amber-500" /> : <Wrench className="w-3 h-3 text-sky-400" />}
                              <span className="text-slate-300">{item.description}</span>
                              <span className="text-slate-600 text-[10px]">x{item.quantity}</span>
                            </div>
                            <span className="font-bold text-slate-400">
                              {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.total)}
                            </span>
                          </div>
                        ))}
                        {(!approvedQuote?.items || approvedQuote.items.length === 0) && (
                          <p className="text-xs text-slate-600 italic">Nenhum item detalhado nesta OS.</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
