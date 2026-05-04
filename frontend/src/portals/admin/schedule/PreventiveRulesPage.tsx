import { useState } from 'react'
import { Plus, Shield, Clock, Gauge, Save, X, Search } from 'lucide-react'
import { useApi } from '@shared/hooks/useApi'
import api from '@core/api/client'
import { TableSkeleton } from '@shared/components/ui'

export default function PreventiveRulesPage() {
  const { data: schedules = [], loading, refetch } = useApi<any[]>(() => api.get('/api/fleet/maintenance'))
  const { data: vehicles = [] } = useApi<any[]>(() => api.get('/api/fleet/vehicles'))
  const { data: boats = [] } = useApi<any[]>(() => api.get('/api/boats'))
  
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [formData, setFormData] = useState<any>({
    service_type: '',
    interval_km: 0,
    interval_days: 0,
    asset_id: '',
    asset_type: 'VEHICLE'
  })

  const handleSave = async () => {
    try {
      const payload = {
        service_type: formData.service_type,
        interval_km: formData.asset_type === 'VEHICLE' ? formData.interval_km : null,
        interval_days: formData.interval_days || null,
        vehicle_id: formData.asset_type === 'VEHICLE' ? parseInt(formData.asset_id) : null,
        boat_id: formData.asset_type === 'BOAT' ? parseInt(formData.asset_id) : null,
        last_done_at: new Date().toISOString().split('T')[0],
        last_done_km: 0
      }
      await api.post('/api/fleet/maintenance', payload)
      setIsModalOpen(false)
      refetch()
    } catch (err) {
      console.error(err)
    }
  }

  if (loading) return <TableSkeleton rows={5} />

  return (
    <div className="space-y-6 animate-fadein pb-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Planos de Preventiva</h1>
          <p className="text-slate-400 text-sm mt-0.5">Configure as regras de manutenção automática da frota.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold flex items-center gap-2 hover:bg-sky-400 transition-all shadow-lg shadow-sky-500/20"
        >
          <Plus className="w-4 h-4" /> Novo Plano
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {schedules.map(s => (
          <div key={s.id} className="bg-navy-800 border border-navy-700 rounded-2xl p-5 flex items-center justify-between group hover:border-navy-600 transition-all">
            <div className="flex items-center gap-5">
              <div className="w-12 h-12 rounded-xl bg-navy-900 border border-navy-700 flex items-center justify-center text-sky-400">
                <Shield className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold text-slate-100">{s.service_type}</h3>
                <div className="flex items-center gap-3 mt-1">
                  {s.interval_km && (
                    <span className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1">
                      <Gauge className="w-3 h-3" /> A cada {s.interval_km.toLocaleString()} km
                    </span>
                  )}
                  {s.interval_days && (
                    <span className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1">
                      <Clock className="w-3 h-3" /> A cada {s.interval_days} dias
                    </span>
                  )}
                </div>
              </div>
            </div>
            
            <div className="text-right">
              <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Vínculo</div>
              <div className="text-xs text-slate-300 font-medium">
                {s.vehicle ? `V: ${s.vehicle.plate}` : s.boat ? `B: ${s.boat.name}` : 'Geral'}
              </div>
            </div>
          </div>
        ))}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-navy-800 border border-navy-700 rounded-3xl w-full max-w-md p-6 shadow-2xl animate-scalein">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-slate-100">Configurar Plano</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-500 hover:text-slate-300 transition-all">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase mb-1.5 block">Tipo de Serviço</label>
                <input 
                  type="text" 
                  placeholder="Ex: Troca de Óleo"
                  className="w-full bg-navy-900 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-sky-500 transition-all"
                  value={formData.service_type}
                  onChange={e => setFormData({...formData, service_type: e.target.value})}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase mb-1.5 block">Intervalo (KM)</label>
                  <input 
                    type="number" 
                    className="w-full bg-navy-900 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-sky-500 transition-all"
                    value={formData.interval_km}
                    onChange={e => setFormData({...formData, interval_km: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase mb-1.5 block">Intervalo (Dias)</label>
                  <input 
                    type="number" 
                    className="w-full bg-navy-900 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-sky-500 transition-all"
                    value={formData.interval_days}
                    onChange={e => setFormData({...formData, interval_days: e.target.value})}
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase mb-1.5 block">Tipo de Ativo</label>
                <div className="flex gap-2 p-1 bg-navy-900 rounded-xl border border-navy-700">
                  <button 
                    onClick={() => setFormData({...formData, asset_type: 'VEHICLE', asset_id: ''})}
                    className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${formData.asset_type === 'VEHICLE' ? 'bg-amber-500 text-navy-950 shadow-lg' : 'text-slate-500'}`}
                  >
                    Veículo
                  </button>
                  <button 
                    onClick={() => setFormData({...formData, asset_type: 'BOAT', asset_id: ''})}
                    className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${formData.asset_type === 'BOAT' ? 'bg-sky-500 text-white shadow-lg' : 'text-slate-500'}`}
                  >
                    Barco
                  </button>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase mb-1.5 block">Selecionar Ativo</label>
                <select 
                  className="w-full bg-navy-900 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-sky-500 transition-all"
                  value={formData.asset_id}
                  onChange={e => setFormData({...formData, asset_id: e.target.value})}
                >
                  <option value="">Selecione...</option>
                  {formData.asset_type === 'VEHICLE' ? (
                    vehicles.map(v => <option key={v.id} value={v.id}>{v.plate} - {v.brand} {v.model}</option>)
                  ) : (
                    boats.map(b => <option key={b.id} value={b.id}>{b.name}</option>)
                  )}
                </select>
              </div>
            </div>

            <div className="flex gap-3 mt-8">
              <button 
                onClick={() => setIsModalOpen(false)}
                className="flex-1 py-3 rounded-xl border border-navy-700 text-slate-400 font-bold text-xs hover:bg-navy-900 transition-all"
              >
                Cancelar
              </button>
              <button 
                onClick={handleSave}
                disabled={!formData.service_type || !formData.asset_id}
                className="flex-1 py-3 rounded-xl bg-sky-500 text-white font-bold text-xs hover:bg-sky-400 transition-all shadow-lg shadow-sky-500/20 disabled:opacity-50"
              >
                Salvar Regra
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
