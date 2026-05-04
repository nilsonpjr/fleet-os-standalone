import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Car, Plus, Search, Wrench, Ship, ChevronRight, Settings } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '@core/api/client'
import { useApi } from '@shared/hooks/useApi'
import { EmptyState, TableSkeleton } from '@shared/components/ui'
import { KpiCard } from '@shared/components/KpiCard'
import { Vehicle } from '@core/types'

function fmtDate(v?: string | null): string {
  if (!v) return '—'
  const dt = new Date(v)
  if (Number.isNaN(dt.getTime())) return v
  return dt.toLocaleDateString('pt-BR')
}

export default function MyFleetPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [assetType, setAssetType] = useState<'VEHICLE' | 'BOAT'>('VEHICLE')
  
  const { data: vehicles = [], loading: loadingVehicles } = useApi<Vehicle[]>(() => api.get('/api/fleet/vehicles'))
  const { data: boats = [], loading: loadingBoats } = useApi<any[]>(() => api.get('/api/boats'))
  const { data: alerts = [] } = useApi<any[]>(() => api.get('/api/fleet/maintenance/alerts'))

  const loading = loadingVehicles || loadingBoats

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase()
    const currentList = assetType === 'VEHICLE' ? vehicles : boats
    if (!needle) return currentList
    return currentList.filter((v: any) => {
      const name = assetType === 'VEHICLE' ? v.plate : v.name
      return name.toLowerCase().includes(needle) || v.brand.toLowerCase().includes(needle) || v.model.toLowerCase().includes(needle)
    })
  }, [vehicles, boats, search, assetType])

  // Get health percentage for an asset
  const getAssetHealth = (assetId: number) => {
    const assetAlert = alerts.find(a => a.id === assetId && a.type === assetType)
    if (!assetAlert) return 100
    // If we have an alert, it means it's > 90% or 100%. We calculate inverse for "Health"
    return Math.max(0, 100 - (assetAlert.usage_percent || 0))
  }

  return (
    <div className="space-y-6 animate-fadein pb-10">
      {/* Header Mobile */}
      <div className="px-1">
        <h1 className="text-2xl font-bold text-slate-100">Minha Frota</h1>
        <p className="text-slate-400 text-sm mt-0.5">Status e manutenção dos seus ativos.</p>
      </div>

      {/* KPI Scroll Horizontal */}
      <div className="flex gap-4 overflow-x-auto pb-4 -mx-1 px-1 custom-scrollbar snap-x">
        <div className="min-w-[280px] snap-center">
          <KpiCard title="Veículos" value={vehicles.length} subtitle="ativos na base" icon={<Car className="w-5 h-5" />} accentColor="amber" loading={loading} />
        </div>
        <div className="min-w-[280px] snap-center">
          <KpiCard title="Embarcações" value={boats.length} subtitle="registradas" icon={<Ship className="w-5 h-5" />} accentColor="sky" loading={loading} />
        </div>
        <div className="min-w-[280px] snap-center">
          <KpiCard title="Alertas" value={alerts.length} subtitle="preventivas pendentes" icon={<AlertTriangle className="w-5 h-5" />} accentColor="red" loading={loading} />
        </div>
      </div>

      {/* Asset Switcher */}
      <div className="bg-navy-900/50 p-1 rounded-2xl border border-navy-700 flex gap-1">
        <button
          onClick={() => setAssetType('VEHICLE')}
          className={`flex-1 py-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            assetType === 'VEHICLE' ? 'bg-navy-800 text-amber-500 shadow-lg' : 'text-slate-500'
          }`}
        >
          <Car className="w-4 h-4" /> Veículos
        </button>
        <button
          onClick={() => setAssetType('BOAT')}
          className={`flex-1 py-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            assetType === 'BOAT' ? 'bg-navy-800 text-sky-400 shadow-lg' : 'text-slate-500'
          }`}
        >
          <Ship className="w-4 h-4" /> Barcos
        </button>
      </div>

      {/* Search Mobile */}
      <div className="relative group">
        <Search className="w-5 h-5 text-slate-500 absolute left-4 top-1/2 -translate-y-1/2 group-focus-within:text-blue-400 transition-colors" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={`Pesquisar ${assetType === 'VEHICLE' ? 'Placa ou Modelo' : 'Nome ou Marca'}...`}
          className="w-full pl-12 pr-4 py-3.5 rounded-2xl bg-navy-900 border border-navy-700 text-sm text-slate-200 outline-none focus:border-blue-500/50 transition-all shadow-inner"
        />
      </div>

      {/* Asset List (Vertical Cards) */}
      <div className="space-y-4">
        {loading ? (
          <TableSkeleton rows={3} />
        ) : filtered.length === 0 ? (
          <EmptyState icon={<Car className="w-8 h-8" />} title="Nada encontrado" description="Tente outro termo de busca." />
        ) : (
          filtered.map((item: any) => {
            const health = getAssetHealth(item.id)
            const isCritical = health < 20
            const isWarning = health < 50
            
            return (
              <div 
                key={item.id} 
                onClick={() => navigate(`/client/fleet/${item.id}?type=${assetType}`)}
                className="bg-navy-900 border border-navy-700 rounded-3xl p-5 active:scale-[0.98] transition-all shadow-xl hover:bg-navy-800/50 cursor-pointer"
              >
                <div className="flex items-start justify-between gap-4 mb-5">
                   <div className="flex items-center gap-4">
                      <div className={`w-14 h-14 rounded-2xl bg-navy-800 border border-navy-700 flex items-center justify-center ${assetType === 'VEHICLE' ? 'text-amber-500 shadow-amber-500/10' : 'text-sky-400 shadow-sky-400/10'} shadow-lg`}>
                        {assetType === 'VEHICLE' ? <Car className="w-7 h-7" /> : <Ship className="w-7 h-7" />}
                      </div>
                      <div>
                        <h3 className="text-lg font-black text-slate-100 uppercase tracking-tighter">
                          {assetType === 'VEHICLE' ? item.plate : item.name}
                        </h3>
                        <p className="text-xs text-slate-500 font-bold uppercase">{item.brand} {item.model}</p>
                      </div>
                   </div>
                   <div className="flex gap-2">
                      <button 
                        onClick={(e) => { e.stopPropagation(); navigate(`/client/requests/new?id=${item.id}&type=${assetType}`) }}
                        className="p-3 rounded-2xl bg-blue-500 text-white shadow-lg shadow-blue-500/20 active:bg-blue-600"
                      >
                         <Plus className="w-5 h-5" />
                      </button>
                   </div>
                </div>

                {/* Health Indicator */}
                <div className="space-y-2 mb-5">
                   <div className="flex justify-between items-center px-1">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Saúde Preventiva</span>
                      <span className={`text-[10px] font-bold ${isCritical ? 'text-red-500' : isWarning ? 'text-amber-500' : 'text-emerald-500'}`}>
                         {Math.round(health)}%
                      </span>
                   </div>
                   <div className="h-2 w-full bg-navy-800 rounded-full overflow-hidden border border-navy-700/50">
                      <div 
                        className={`h-full rounded-full transition-all duration-700 ${isCritical ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : isWarning ? 'bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]' : 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]'}`}
                        style={{ width: `${health}%` }}
                      />
                   </div>
                </div>

                {/* Tags Row */}
                <div className="flex flex-wrap gap-2 pt-4 border-t border-navy-700/50">
                   <div className="px-3 py-1.5 rounded-xl bg-navy-800 border border-navy-700 flex items-center gap-2">
                      <Settings className="w-3.5 h-3.5 text-slate-500" />
                      <span className="text-[10px] font-bold text-slate-300 uppercase">
                        {assetType === 'VEHICLE' ? `${item.mileage_current || 0} KM` : `${item.hours_current || 0} H`}
                      </span>
                   </div>
                   <div className="flex-1" />
                   <div className="flex items-center gap-2 text-blue-400">
                      <span className="text-[10px] font-bold uppercase tracking-wider">Histórico</span>
                      <ChevronRight className="w-4 h-4" />
                   </div>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
