import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  ArrowLeft, Car, Calendar, Shield, CreditCard, 
  Settings, History, AlertTriangle, CheckCircle2,
  MapPin, Gauge, Fuel, Info
} from 'lucide-react'
import api from '@core/api/client'
import { StatusBadge, TableSkeleton, EmptyState } from '@shared/components/ui'
import { KpiCard } from '@shared/components/KpiCard'

interface VehicleDetail {
  id: number
  client_id: number | null
  plate: string
  brand: string
  model: string
  category: string
  year_model: number | null
  year_manufacture: number | null
  color: string | null
  fuel_type: string | null
  renavam: string | null
  chassis: string | null
  mileage_current: number
  mileage_last_maint: number | null
  ipva_due_date: string | null
  ipva_value: number | null
  licensing_due_date: string | null
  licensing_year: number | null
  licensing_paid: boolean
  insurance_policy: string | null
  insurance_company: string | null
  insurance_expiry: string | null
  insurance_value: number | null
  usage_type: string | null
  notes: string | null
  is_active: boolean
  client?: {
    id: number
    name: string
  }
  last_lat: number | null
  last_lng: number | null
  last_sync_at: string | null
}

interface RequestSummary {
  id: number
  status: string
  problem_description: string
  created_at: string
}

import AssetHistoryTab from '@shared/components/AssetHistoryTab'
import AssetCostStats from '@shared/components/AssetCostStats'
import AssetHealthCard from '@shared/components/AssetHealthCard'

export default function VehicleDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [vehicle, setVehicle] = useState<VehicleDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'GERAL' | 'HISTORY' | 'STATS'>('GERAL')

  const loadData = async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<VehicleDetail>(`/api/fleet/vehicles/${id}`)
      setVehicle(data)
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Falha ao carregar detalhes do veículo')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [id])

  if (loading) return <TableSkeleton rows={10} cols={1} />
  if (error || !vehicle) {
    return (
      <EmptyState 
        icon={<AlertTriangle className="w-10 h-10 text-red-500" />}
        title="Erro ao carregar"
        description={error || "Veículo não encontrado"}
      />
    )
  }

  const fmtDate = (v?: string | null) => {
    if (!v) return '—'
    return new Date(v).toLocaleDateString('pt-BR')
  }

  const fmtCurrency = (v?: number | null) => {
    if (v === null || v === undefined) return '—'
    return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  }

  return (
    <div className="space-y-6 animate-fadein pb-10">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/admin/vehicles')}
            className="p-2 rounded-xl bg-navy-800 border border-navy-700 text-slate-400 hover:bg-navy-700 transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-100 font-plate uppercase tracking-wider">{vehicle.plate}</h1>
              <StatusBadge status={vehicle.is_active ? 'ACTIVE' : 'INACTIVE'} map={{
                ACTIVE: 'status-approved',
                INACTIVE: 'status-open'
              }} />
            </div>
            <p className="text-slate-400 text-sm mt-0.5">
              {vehicle.brand} {vehicle.model} • {vehicle.year_model || vehicle.year_manufacture || '—'}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard 
          title="Km Atual"
          value={vehicle.mileage_current}
          subtitle={`Última manut.: ${vehicle.mileage_last_maint ?? '—'} km`}
          icon={<Gauge className="w-5 h-5" />}
          accentColor="amber"
        />
        <KpiCard 
          title="IPVA"
          value={fmtCurrency(vehicle.ipva_value)}
          subtitle={`Vence: ${fmtDate(vehicle.ipva_due_date)}`}
          icon={<CreditCard className="w-5 h-5" />}
          accentColor="blue"
        />
        <KpiCard 
          title="Licenciamento"
          value={vehicle.licensing_year || '—'}
          subtitle={vehicle.licensing_paid ? 'Pago ✅' : `Vence: ${fmtDate(vehicle.licensing_due_date)}`}
          icon={<Calendar className="w-5 h-5" />}
          accentColor={vehicle.licensing_paid ? 'emerald' : 'red'}
        />
        <KpiCard 
          title="Seguro"
          value={vehicle.insurance_company || 'N/A'}
          subtitle={`Expira: ${fmtDate(vehicle.insurance_expiry)}`}
          icon={<Shield className="w-5 h-5" />}
          accentColor="sky"
        />
      </div>

      <div className="flex border-b border-navy-700 gap-6">
        <button
          onClick={() => setActiveTab('GERAL')}
          className={`pb-4 text-sm font-bold transition-all border-b-2 ${activeTab === 'GERAL' ? 'border-amber-500 text-amber-500' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
        >
          Ficha Técnica
        </button>
        <button
          onClick={() => setActiveTab('HISTORY')}
          className={`pb-4 text-sm font-bold transition-all border-b-2 ${activeTab === 'HISTORY' ? 'border-amber-500 text-amber-500' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
        >
          Histórico
        </button>
        <button
          onClick={() => setActiveTab('STATS')}
          className={`pb-4 text-sm font-bold transition-all border-b-2 ${activeTab === 'STATS' ? 'border-amber-500 text-amber-500' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
        >
          Estatísticas
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {activeTab === 'GERAL' ? (
            <>
              <AssetHealthCard vehicleId={vehicle.id} />
              {/* Identificação */}
              <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-6 border-b border-navy-700 pb-4">
                  <Car className="w-5 h-5 text-amber-500" />
                  <h3 className="font-bold text-slate-100">Dados de Identificação</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-6 gap-x-10">
                  <InfoItem label="Marca" value={vehicle.brand} />
                  <InfoItem label="Modelo" value={vehicle.model} />
                  <InfoItem label="Ano Modelo" value={vehicle.year_model} />
                  <InfoItem label="Ano Fabricação" value={vehicle.year_manufacture} />
                  <InfoItem label="Categoria" value={vehicle.category} />
                  <InfoItem label="Cor" value={vehicle.color} />
                  <InfoItem label="RENAVAM" value={vehicle.renavam} copyable />
                  <InfoItem label="Chassi" value={vehicle.chassis} copyable />
                </div>
              </div>

              {/* Operação e Notas */}
              <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-6 border-b border-navy-700 pb-4">
                  <Settings className="w-5 h-5 text-emerald-500" />
                  <h3 className="font-bold text-slate-100">Operação</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-6 gap-x-10 mb-8">
                  <InfoItem label="Tipo de Uso" value={vehicle.usage_type} />
                  <InfoItem label="Combustível" value={vehicle.fuel_type} />
                  <InfoItem label="Km Inicial" value={vehicle.mileage_last_maint} />
                  <InfoItem label="Status Sistema" value={vehicle.is_active ? 'Ativo' : 'Desativado'} />
                </div>
                <div className="space-y-2 pt-4 border-t border-navy-700">
                  <label className="text-xs font-bold uppercase text-slate-500">Observações Internas</label>
                  <p className="text-sm text-slate-300 leading-relaxed italic">
                    {vehicle.notes || "Nenhuma observação registrada."}
                  </p>
                </div>
              </div>
            </>
          ) : activeTab === 'HISTORY' ? (
            <AssetHistoryTab vehicleId={vehicle.id} />
          ) : (
            <AssetCostStats vehicleId={vehicle.id} />
          )}
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          {/* Proprietário */}
          <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-6 border-b border-navy-700 pb-4">
              <Info className="w-5 h-5 text-amber-500" />
              <h3 className="font-bold text-slate-100">Proprietário</h3>
            </div>
            {vehicle.client ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500 font-bold">
                    {vehicle.client.name.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-100">{vehicle.client.name}</p>
                    <p className="text-xs text-slate-500">ID #{vehicle.client.id}</p>
                  </div>
                </div>
                <button 
                  onClick={() => navigate(`/admin/clients/${vehicle.client?.id}`)}
                  className="w-full py-2 rounded-xl border border-navy-700 text-xs font-bold text-slate-400 hover:bg-navy-700 transition-all"
                >
                  Ver Ficha do Cliente
                </button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-xs text-slate-500 italic">Veículo sem proprietário vinculado (Uso Interno)</p>
              </div>
            )}
          </div>

          {/* Telemetry (IoT) */}
          <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6 border-b border-navy-700 pb-4">
              <div className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-blue-500" />
                <h3 className="font-bold text-slate-100">Localização IoT</h3>
              </div>
              {vehicle.last_sync_at && (
                <span className="text-[9px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-1 rounded-full animate-pulse">
                  SINCRONIZADO
                </span>
              )}
            </div>
            
            <div className="space-y-4">
               {vehicle.last_lat ? (
                 <>
                   <div className="aspect-video bg-navy-900 rounded-xl overflow-hidden relative border border-navy-700">
                      {/* Simulação de Mapa */}
                      <div className="absolute inset-0 opacity-40 bg-[url('https://api.mapbox.com/styles/v1/mapbox/dark-v10/static/-46.6333,-23.5505,12,0/400x300?access_token=mock')] bg-cover" />
                      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                         <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center border-2 border-white shadow-lg animate-bounce">
                            <Car className="w-3 h-3 text-white" />
                         </div>
                      </div>
                      <div className="absolute bottom-2 left-2 bg-black/60 backdrop-blur-md px-2 py-1 rounded text-[10px] text-white">
                         Lat: {vehicle.last_lat.toFixed(4)} | Lng: {vehicle.last_lng?.toFixed(4)}
                      </div>
                   </div>
                   <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Último sinal</span>
                      <span className="text-slate-300 font-medium">{new Date(vehicle.last_sync_at!).toLocaleString('pt-BR')}</span>
                   </div>
                 </>
               ) : (
                 <div className="aspect-video bg-navy-900/50 border border-dashed border-navy-700 rounded-xl flex flex-col items-center justify-center text-center p-4">
                    <MapPin className="w-8 h-8 text-slate-700 mb-2" />
                    <p className="text-xs text-slate-600 italic">Nenhum dado de telemetria recebido ainda para este veículo.</p>
                 </div>
               )}
            </div>
          </div>

          {/* Resumo de Custos */}
          <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-6 border-b border-navy-700 pb-4">
              <Fuel className="w-5 h-5 text-blue-500" />
              <h3 className="font-bold text-slate-100">Custos Anuais Est.</h3>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-500">IPVA</span>
                <span className="text-sm font-medium text-slate-200">{fmtCurrency(vehicle.ipva_value)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-500">Seguro</span>
                <span className="text-sm font-medium text-slate-200">{fmtCurrency(vehicle.insurance_value)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-500">Licenciamento</span>
                <span className="text-sm font-medium text-slate-200">R$ 150,00</span>
              </div>
              <div className="pt-4 border-t border-navy-700 flex justify-between items-center">
                <span className="text-sm font-bold text-slate-100">Total Fixo</span>
                <span className="text-lg font-bold text-amber-500">
                  {fmtCurrency((vehicle.ipva_value || 0) + (vehicle.insurance_value || 0) + 150)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function InfoItem({ label, value, copyable }: { label: string, value: any, copyable?: boolean }) {
  const val = value === null || value === undefined || value === '' ? '—' : value.toString()
  
  return (
    <div className="space-y-1">
      <label className="text-[10px] font-bold uppercase text-slate-500 tracking-wider block">{label}</label>
      <div className="flex items-center justify-between group">
        <span className={`text-sm text-slate-100 font-medium ${copyable ? 'font-mono' : ''}`}>
          {val}
        </span>
        {copyable && val !== '—' && (
          <button 
            onClick={() => navigator.clipboard.writeText(val)}
            className="opacity-0 group-hover:opacity-100 text-amber-500 text-[10px] font-bold uppercase p-1 hover:bg-amber-500/10 rounded transition-all"
          >
            Copiar
          </button>
        )}
      </div>
    </div>
  )
}
