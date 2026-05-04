import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, Car, Ship, MapPin, Gauge, Fuel, Calendar, Shield } from 'lucide-react'
import { useApi } from '@shared/hooks/useApi'
import api from '@core/api/client'
import AssetHistoryTab from '@shared/components/AssetHistoryTab'
import AssetCostStats from '@shared/components/AssetCostStats'
import { TableSkeleton } from '@shared/components/ui'

export default function AssetDetailPage() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const type = searchParams.get('type') || 'VEHICLE'

  const { data: asset, loading } = useApi<any>(() => 
    type === 'VEHICLE' ? api.get(`/api/fleet/vehicles/${id}`) : api.get(`/api/boats/${id}`)
  )

  if (loading) return <TableSkeleton rows={5} />
  if (!asset) return <div className="p-10 text-center text-slate-500">Ativo não encontrado.</div>

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadein pb-20">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button 
          onClick={() => navigate(-1)}
          className="p-3 rounded-2xl bg-navy-900 border border-navy-700 text-slate-400 hover:text-slate-200 transition-all shadow-lg"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <div className="flex items-center gap-3">
             <h1 className="text-3xl font-black text-slate-100 uppercase tracking-tighter">
                {type === 'VEHICLE' ? asset.plate : asset.name}
             </h1>
             {type === 'VEHICLE' ? <Car className="w-6 h-6 text-amber-500" /> : <Ship className="w-6 h-6 text-sky-400" />}
          </div>
          <p className="text-slate-400 text-sm font-bold uppercase tracking-widest">{asset.brand} {asset.model} · {asset.year_model || asset.year}</p>
        </div>
      </div>

      {/* Stats Section */}
      <div className="space-y-4">
        <h2 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Análise de Custos</h2>
        <AssetCostStats 
          vehicleId={type === 'VEHICLE' ? parseInt(id!) : undefined} 
          boatId={type === 'BOAT' ? parseInt(id!) : undefined} 
        />
      </div>

      {/* Main Tabs (Simulated as sections for mobile-first feel) */}
      <div className="space-y-6">
        
        {/* Info Cards */}
        <div className="grid grid-cols-2 gap-4">
           <div className="bg-navy-900/40 border border-navy-700/50 rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-2 text-slate-500">
                 {type === 'VEHICLE' ? <Gauge className="w-4 h-4" /> : <Calendar className="w-4 h-4" />}
                 <span className="text-[10px] font-bold uppercase">Uso Atual</span>
              </div>
              <p className="text-lg font-bold text-slate-200">
                 {type === 'VEHICLE' ? `${asset.mileage_current || 0} KM` : `${asset.hours_current || 0} Horas`}
              </p>
           </div>
           <div className="bg-navy-900/40 border border-navy-700/50 rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-2 text-slate-500">
                 <Shield className="w-4 h-4" />
                 <span className="text-[10px] font-bold uppercase">Seguro</span>
              </div>
              <p className="text-sm font-bold text-slate-200 truncate">
                 {asset.insurance_company || 'Não informado'}
              </p>
           </div>
        </div>

        {/* History Section */}
        <div className="space-y-4">
          <h2 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Linha do Tempo de Manutenção</h2>
          <div className="bg-navy-800 border border-navy-700 rounded-3xl p-6 shadow-xl">
            <AssetHistoryTab 
              vehicleId={type === 'VEHICLE' ? parseInt(id!) : undefined} 
              boatId={type === 'BOAT' ? parseInt(id!) : undefined} 
            />
          </div>
        </div>

      </div>
    </div>
  )
}
