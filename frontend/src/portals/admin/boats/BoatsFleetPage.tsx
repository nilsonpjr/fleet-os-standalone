import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Search, Ship, User, ChevronRight, Anchor, AlertTriangle } from 'lucide-react'
import api from '@core/api/client'
import { useApi } from '@shared/hooks/useApi'
import { EmptyState, TableSkeleton, StatusBadge } from '@shared/components/ui'
import { CreateBoatModal } from './components/CreateBoatModal'

export default function BoatsFleetPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [filterType, setFilterType] = useState('TODOS')
  
  const { data: boats = [], loading, error, refetch } = useApi<any[]>(() => 
    api.get('/api/boats')
  )

  const filtered = useMemo(() => {
    let result = boats
    const needle = search.trim().toLowerCase()
    
    if (needle) {
      result = result.filter((b) =>
        b.name.toLowerCase().includes(needle) ||
        b.brand?.toLowerCase().includes(needle) ||
        b.model?.toLowerCase().includes(needle) ||
        b.client?.name?.toLowerCase().includes(needle)
      )
    }

    if (filterType !== 'TODOS') {
      result = result.filter(b => (b.type || 'LANCHA') === filterType)
    }

    return result
  }, [boats, search, filterType])

  const checkAlerts = (b: any) => {
    const dates = [b.tmc_expiration, b.insurance_expiration, b.antf_expiration]
    const now = new Date()
    return dates.some(d => {
      if (!d) return false
      const expiry = new Date(d)
      const diff = expiry.getTime() - now.getTime()
      return diff < (30 * 24 * 60 * 60 * 1000) // 30 days
    })
  }

  return (
    <div className="space-y-6 animate-fadein">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Ship className="w-6 h-6 text-sky-400" />
            Frota de Embarcações
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">Gerencie lanchas, veleiros e jet-skis da frota.</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-sky-500 text-white font-bold hover:bg-sky-400 transition-all text-sm shadow-lg shadow-sky-500/10"
        >
          <Plus className="w-4 h-4" />
          Cadastrar Embarcação
        </button>
      </div>

      <div className="bg-navy-800 border border-navy-700 rounded-2xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between shadow-xl shadow-black/10">
        <div className="relative w-full max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por nome, marca, modelo ou cliente..."
            className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-navy-900 border border-navy-700 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500/40"
          />
        </div>
        
        <div className="flex gap-2">
          {['TODOS', 'LANCHA', 'VELEIRO', 'JET-SKI'].map(type => (
            <button 
              key={type} 
              onClick={() => setFilterType(type)}
              className={`px-3 py-1.5 rounded-lg border text-[10px] font-bold transition-all uppercase ${
                filterType === type 
                ? 'bg-sky-500/20 border-sky-500 text-sky-400' 
                : 'border-navy-700 text-slate-500 hover:text-slate-300'
              }`}
            >
              {type}
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
        <TableSkeleton rows={5} cols={5} />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Ship className="w-10 h-10" />}
          title="Nenhuma embarcação encontrada"
          description={search ? "Tente ajustar sua busca." : "Ainda não há barcos cadastrados no sistema."}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((b) => (
            <div 
              key={b.id} 
              onClick={() => navigate(`/admin/boats/${b.id}`)}
              className="bg-navy-800 border border-navy-700 rounded-2xl p-5 hover:border-sky-500/50 transition-all cursor-pointer group flex flex-col h-full shadow-lg hover:shadow-sky-500/5"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
                    <Ship className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-slate-100 font-bold leading-tight">{b.name}</h3>
                    <p className="text-[10px] text-slate-500 uppercase tracking-tighter font-bold">{b.brand} {b.model} • {b.year}</p>
                  </div>
                </div>
                {checkAlerts(b) && (
                  <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center text-red-400 animate-pulse">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                )}
              </div>

              <div className="space-y-2.5 flex-1">
                <div className="flex items-center justify-between p-2 rounded-xl bg-navy-900/50 border border-navy-700/50">
                  <div className="flex items-center gap-2 text-[9px] font-bold text-slate-500 uppercase tracking-widest">
                    <User className="w-3 h-3 text-sky-500" />
                    Proprietário
                  </div>
                  <span className="text-xs text-slate-200 font-medium truncate max-w-[120px]">{b.client?.name || 'Vago'}</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-xl bg-navy-900/50 border border-navy-700/50">
                  <div className="flex items-center gap-2 text-[9px] font-bold text-slate-500 uppercase tracking-widest">
                    <Anchor className="w-3 h-3 text-sky-500" />
                    TMC (Registro)
                  </div>
                  <span className="text-xs text-slate-200 font-plate">{b.registration_number || '—'}</span>
                </div>
              </div>

              <div className="mt-5 pt-4 border-t border-navy-700/50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <StatusBadge 
                    status={checkAlerts(b) ? 'CANCELADO' : 'CONCLUÍDO'} 
                    label={b.type || 'LANCHA'} 
                  />
                </div>
                <div className="flex items-center gap-1 text-slate-600 group-hover:text-sky-400 transition-colors">
                  <span className="text-[10px] font-bold uppercase tracking-widest">Detalhes</span>
                  <ChevronRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <CreateBoatModal 
          onClose={() => setShowCreate(false)} 
          onSuccess={() => {
            refetch()
            setShowCreate(false)
          }} 
        />
      )}
    </div>
  )
}
