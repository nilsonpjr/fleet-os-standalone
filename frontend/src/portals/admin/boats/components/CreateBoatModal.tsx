import { useState, useEffect } from 'react'
import { X, Save, Ship, Anchor, Shield, User, FileText } from 'lucide-react'
import api from '@core/api/client'

interface CreateBoatModalProps {
  onClose: () => void
  onSuccess: () => void
  initialData?: any
}

export function CreateBoatModal({ onClose, onSuccess, initialData }: CreateBoatModalProps) {
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState(0)
  const [clients, setClients] = useState<{ id: number; name: string }[]>([])
  const [formData, setFormData] = useState({
    name: initialData?.name || '',
    type: initialData?.type || 'LANCHA',
    brand: initialData?.brand || '',
    model: initialData?.model || '',
    year: initialData?.year || new Date().getFullYear(),
    registration_number: initialData?.registration_number || '',
    tmc_expiration: initialData?.tmc_expiration || '',
    insurance_expiration: initialData?.insurance_expiration || '',
    antf_expiration: initialData?.antf_expiration || '',
    client_id: initialData?.client_id || '',
    engine_type: initialData?.engine_type || 'CENTRO-RABETA',
    fuel_type: initialData?.fuel_type || 'DIESEL',
  })

  const tabs = [
    { label: 'Identificação', icon: Ship },
    { label: 'Regulatório', icon: Anchor },
    { label: 'Proprietário', icon: User },
  ]

  useEffect(() => {
    api.get<{ id: number; name: string }[]>('/api/clients')
       .then(setClients)
       .catch(console.error)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (initialData?.id) {
        await api.put(`/api/boats/${initialData.id}`, formData)
      } else {
        await api.post('/api/boats', formData)
      }
      onSuccess()
      onClose()
    } catch (err) {
      console.error(err)
      alert('Erro ao salvar embarcação')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadein">
      <div className="bg-navy-900 border border-navy-700 w-full max-w-2xl rounded-3xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="p-6 border-b border-navy-700 flex justify-between items-center bg-navy-800/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
              <Ship className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100">{initialData ? 'Editar Embarcação' : 'Nova Embarcação'}</h2>
              <p className="text-xs text-slate-500 uppercase tracking-widest font-bold">Cadastro de Frota</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-navy-700 rounded-xl transition-colors text-slate-400">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-navy-700 bg-navy-800/30">
          {tabs.map((tab, idx) => (
            <button
              key={idx}
              onClick={() => setActiveTab(idx)}
              className={`flex-1 flex items-center justify-center gap-2 py-4 text-xs font-bold transition-all border-b-2 ${
                activeTab === idx 
                ? 'border-sky-500 text-sky-400 bg-sky-500/5' 
                : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span className="uppercase tracking-wider">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-8 space-y-6">
          {activeTab === 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-slidein">
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase">Nome da Embarcação</label>
                <input
                  required
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-3 text-slate-200 focus:ring-2 focus:ring-sky-500/40 outline-none transition-all"
                  placeholder="Ex: Maré Alta III"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase">Tipo</label>
                <select
                  value={formData.type}
                  onChange={e => setFormData({...formData, type: e.target.value})}
                  className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-3 text-slate-200 focus:ring-2 focus:ring-sky-500/40 outline-none transition-all"
                >
                  <option value="LANCHA">Lancha</option>
                  <option value="VELEIRO">Veleiro</option>
                  <option value="JET-SKI">Jet-Ski</option>
                  <option value="IATE">Iate</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase">Marca</label>
                <input
                  value={formData.brand}
                  onChange={e => setFormData({...formData, brand: e.target.value})}
                  className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-3 text-slate-200 focus:ring-2 focus:ring-sky-500/40 outline-none transition-all"
                  placeholder="Ex: Azimut"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase">Modelo</label>
                <input
                  value={formData.model}
                  onChange={e => setFormData({...formData, model: e.target.value})}
                  className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-3 text-slate-200 focus:ring-2 focus:ring-sky-500/40 outline-none transition-all"
                  placeholder="Ex: 60ft"
                />
              </div>
            </div>
          )}

          {activeTab === 1 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-slidein">
              <div className="space-y-2 md:col-span-2">
                <label className="text-xs font-bold text-slate-500 uppercase">Número de Inscrição (TMC)</label>
                <div className="relative">
                  <Anchor className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input
                    value={formData.registration_number}
                    onChange={e => setFormData({...formData, registration_number: e.target.value})}
                    className="w-full bg-navy-800 border border-navy-700 rounded-xl pl-11 pr-4 py-3 text-slate-200 font-plate tracking-wider"
                    placeholder="000A000000"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-tighter">Vencimento TMC</label>
                <input
                  type="date"
                  value={formData.tmc_expiration}
                  onChange={e => setFormData({...formData, tmc_expiration: e.target.value})}
                  className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-3 text-slate-200"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-tighter">Seguro DPEM</label>
                <input
                  type="date"
                  value={formData.insurance_expiration}
                  onChange={e => setFormData({...formData, insurance_expiration: e.target.value})}
                  className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-3 text-slate-200"
                />
              </div>
            </div>
          )}

          {activeTab === 2 && (
            <div className="space-y-6 animate-slidein">
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase">Vincular Cliente</label>
                <select
                  value={formData.client_id}
                  onChange={e => setFormData({...formData, client_id: e.target.value})}
                  className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-3 text-slate-200"
                >
                  <option value="">Selecione um cliente...</option>
                  {clients.map(c => (
                    <option key={c.id} value={c.id}>{c.name} (ID #{c.id})</option>
                  ))}
                </select>
              </div>
              <div className="p-4 rounded-2xl bg-amber-500/5 border border-amber-500/10 flex gap-4">
                <div className="p-2 rounded-lg bg-amber-500/10 text-amber-500 h-fit">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-amber-200">Nota Fiscal</h4>
                  <p className="text-xs text-amber-500/70">O vínculo de propriedade é essencial para faturamento de serviços e peças.</p>
                </div>
              </div>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="p-6 border-t border-navy-700 bg-navy-800/50 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-6 py-3 rounded-xl border border-navy-700 text-slate-400 font-bold hover:bg-navy-700 transition-all uppercase text-xs tracking-widest"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="flex-[2] flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-sky-500 text-white font-bold hover:bg-sky-400 transition-all shadow-lg shadow-sky-500/20 uppercase text-xs tracking-widest disabled:opacity-50"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white animate-spin rounded-full" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Salvar Embarcação
          </button>
        </div>
      </div>
    </div>
  )
}
