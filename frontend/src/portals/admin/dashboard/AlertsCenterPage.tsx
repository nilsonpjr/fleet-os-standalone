import { useState, useMemo } from 'react'
import { AlertTriangle, Bell, Clock, Gauge, Search, Filter, ShieldAlert, ChevronRight, FileText, Wrench } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useApi } from '@shared/hooks/useApi'
import api from '@core/api/client'
import { TableSkeleton } from '@shared/components/ui'

export default function AlertsCenterPage() {
  const navigate = useNavigate()
  const [filter, setFilter] = useState<'ALL' | 'EXPIRY' | 'MAINTENANCE'>('ALL')
  
  const { data: expiryAlerts = [], loading: loadingExpiry } = useApi<any[]>(() => api.get('/api/fleet/alerts'))
  const { data: maintAlerts = [], loading: loadingMaint } = useApi<any[]>(() => api.get('/api/fleet/maintenance/alerts'))

  const loading = loadingExpiry || loadingMaint

  const allAlerts = useMemo(() => {
    const list: any[] = []
    
    // Process Expiry Alerts
    expiryAlerts.forEach(a => {
      list.push({
        id: `exp-${a.assetName}-${a.type}`,
        category: 'EXPIRY',
        title: a.type,
        subtitle: a.assetName,
        plate: a.plate,
        dueDate: a.dueDate,
        daysLeft: a.daysLeft,
        criticality: a.daysLeft <= 5 ? 'HIGH' : 'MEDIUM'
      })
    })

    // Process Maintenance Alerts
    maintAlerts.forEach(m => {
      list.push({
        id: `maint-${m.asset_name}-${m.service_type}`,
        category: 'MAINTENANCE',
        title: `PREVENTIVA: ${m.service_type}`,
        subtitle: m.asset_name,
        reason: m.reason,
        usage: m.usage_percent,
        criticality: m.usage_percent >= 100 ? 'HIGH' : 'MEDIUM'
      })
    })

    return list.sort((a, b) => {
      if (a.criticality === 'HIGH' && b.criticality !== 'HIGH') return -1
      if (a.criticality !== 'HIGH' && b.criticality === 'HIGH') return 1
      return 0
    })
  }, [expiryAlerts, maintAlerts])

  const filtered = allAlerts.filter(a => {
    if (filter === 'ALL') return true
    return a.category === filter
  })

  return (
    <div className="space-y-6 animate-fadein pb-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Bell className="w-6 h-6 text-red-500" /> Central de Alertas
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">Monitoramento em tempo real de documentos e manutenção.</p>
        </div>
        <div className="flex gap-1 bg-navy-800 p-1 rounded-xl border border-navy-700">
           {['ALL', 'EXPIRY', 'MAINTENANCE'].map((f) => (
             <button
               key={f}
               onClick={() => setFilter(f as any)}
               className={`px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase transition-all ${
                 filter === f ? 'bg-navy-900 text-slate-100 shadow-lg' : 'text-slate-500 hover:text-slate-300'
               }`}
             >
               {f === 'ALL' ? 'Todos' : f === 'EXPIRY' ? 'Documentos' : 'Manutenção'}
             </button>
           ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {loading ? (
          <TableSkeleton rows={6} />
        ) : filtered.length === 0 ? (
          <div className="py-20 text-center bg-navy-900/30 rounded-3xl border-2 border-dashed border-navy-800">
             <ShieldAlert className="w-12 h-12 text-slate-700 mx-auto mb-4" />
             <p className="text-slate-500 font-medium">Nenhum alerta crítico no momento.</p>
          </div>
        ) : (
          filtered.map((alert) => (
            <div 
              key={alert.id}
              className={`bg-navy-800 border-l-4 rounded-2xl p-5 flex items-center justify-between transition-all hover:bg-navy-700/30 ${
                alert.criticality === 'HIGH' ? 'border-l-red-500 border-navy-700' : 'border-l-amber-500 border-navy-700'
              }`}
            >
               <div className="flex items-center gap-5">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${
                    alert.category === 'EXPIRY' ? 'bg-amber-500/10 text-amber-500' : 'bg-sky-500/10 text-sky-500'
                  }`}>
                    {alert.category === 'EXPIRY' ? <FileText className="w-6 h-6" /> : <Gauge className="w-6 h-6" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                       <h3 className="font-bold text-slate-100">{alert.title}</h3>
                       {alert.criticality === 'HIGH' && (
                         <span className="bg-red-500/20 text-red-500 text-[8px] font-black uppercase px-1.5 py-0.5 rounded ring-1 ring-red-500/30 animate-pulse">Crítico</span>
                       )}
                    </div>
                    <p className="text-xs text-slate-400">{alert.subtitle} {alert.plate ? `· ${alert.plate}` : ''}</p>
                  </div>
               </div>

               <div className="flex items-center gap-8">
                  <div className="text-right hidden sm:block">
                     <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-0.5">Status</p>
                     <p className={`text-xs font-black ${alert.criticality === 'HIGH' ? 'text-red-400' : 'text-amber-400'}`}>
                        {alert.category === 'EXPIRY' 
                          ? `Vence em ${alert.daysLeft} dias` 
                          : `${Math.round(alert.usage || 0)}% de uso`
                        }
                     </p>
                  </div>
                  <button 
                    onClick={() => navigate('/admin/requests')}
                    className="p-3 rounded-xl bg-navy-900 border border-navy-700 text-slate-400 hover:text-slate-100 hover:border-navy-600 transition-all flex items-center gap-2"
                  >
                     <Wrench className="w-4 h-4" />
                     <span className="text-xs font-bold hidden md:inline">Agendar</span>
                     <ChevronRight className="w-4 h-4" />
                  </button>
               </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
