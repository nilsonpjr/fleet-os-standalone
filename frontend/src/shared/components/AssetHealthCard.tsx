import { useMemo } from 'react'
import { CheckCircle2, AlertTriangle, Clock, Gauge } from 'lucide-react'
import { useApi } from '@shared/hooks/useApi'
import api from '@core/api/client'

interface AssetHealthCardProps {
  vehicleId?: number
  boatId?: number
}

export default function AssetHealthCard({ vehicleId, boatId }: AssetHealthCardProps) {
  const { data: schedules = [], loading } = useApi<any[]>(() => 
    api.get('/api/fleet/maintenance', { vehicle_id: vehicleId, boat_id: boatId })
  )

  if (loading) return <div className="h-40 animate-pulse bg-navy-900/50 rounded-2xl" />

  if (schedules.length === 0) {
    return (
      <div className="p-8 text-center border-2 border-dashed border-navy-700 rounded-2xl">
        <CheckCircle2 className="w-10 h-10 text-slate-700 mx-auto mb-2" />
        <p className="text-slate-500 text-sm">Nenhum plano de manutenção configurado.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
        <Gauge className="w-4 h-4 text-sky-400" /> Saúde do Ativo & Preventiva
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {schedules.map(s => {
          // Mock progress calculation if actual data is missing
          const interval = s.interval_km || s.interval_days || 10000
          const done = s.last_done_km || 0
          // For demo, let's assume we are at 85% if no current mileage is passed here
          // In real app, we'd compare with current mileage from the parent
          const progress = Math.min(Math.round((done / interval) * 100), 100)
          const isWarning = progress >= 90

          return (
            <div key={s.id} className="p-4 rounded-2xl bg-navy-900 border border-navy-700 space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-sm font-bold text-slate-200">{s.service_type}</div>
                {isWarning ? (
                  <div className="flex items-center gap-1 text-[10px] font-bold text-amber-500 uppercase">
                    <AlertTriangle className="w-3 h-3" /> Atenção
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-[10px] font-bold text-emerald-500 uppercase">
                    <CheckCircle2 className="w-3 h-3" /> Em Dia
                  </div>
                )}
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-[10px] font-bold uppercase">
                  <span className="text-slate-500">Uso: {done.toLocaleString()} / {interval.toLocaleString()} {s.interval_km ? 'km' : 'dias'}</span>
                  <span className={isWarning ? 'text-amber-500' : 'text-slate-400'}>{progress}%</span>
                </div>
                <div className="h-1.5 w-full bg-navy-800 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-1000 ${isWarning ? 'bg-amber-500' : 'bg-sky-500'}`}
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 text-[10px] text-slate-500">
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" /> Última: {s.last_done_at || 'N/A'}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
