import { useState, FormEvent } from 'react'
import { X, Wrench, Shield, MapPin, Phone, User, Save, Star, Activity } from 'lucide-react'

interface WorkshopFormModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: any) => void
  initialData?: any
  loading?: boolean
}

export default function WorkshopFormModal({ isOpen, onClose, onSave, initialData, loading }: WorkshopFormModalProps) {
  const [activeTab, setActiveTab] = useState('IDENT')
  const [formData, setFormData] = useState(initialData || {
    name: '',
    cnpj: '',
    ie: '',
    phone: '',
    email: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    contact_name: '',
    specialties_csv: '',
    vehicle_types_csv: '',
    rating: '5',
    max_concurrent_os: '5',
    notes: '',
    partner_id: '',
  })

  if (!isOpen) return null

  const tabs = [
    { id: 'IDENT', label: 'Identificação', icon: Wrench },
    { id: 'ADDR',  label: 'Localização', icon: MapPin },
    { id: 'OPER',  label: 'Operação', icon: Activity },
    { id: 'FISCAL', label: 'Fiscal', icon: Shield },
  ]

  const handleChange = (e: any) => {
    const { name, value } = e.target
    setFormData((prev: any) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    onSave(formData)
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadein">
      <div className="bg-navy-900 border border-navy-700 rounded-3xl w-full max-w-4xl h-[600px] flex overflow-hidden shadow-2xl animate-scalein">
        {/* Sidebar Tabs */}
        <div className="w-64 bg-navy-800/50 border-r border-navy-700 p-4 space-y-2 flex flex-col">
          <div className="mb-6 px-2">
            <h2 className="text-lg font-bold text-slate-100">Cadastro de Oficina</h2>
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mt-1">Parceiros FleetOS</p>
          </div>
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-xs font-bold transition-all ${
                activeTab === tab.id 
                  ? 'bg-amber-500 text-navy-950 shadow-lg shadow-amber-500/20' 
                  : 'text-slate-400 hover:bg-navy-700/50'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
          
          <div className="mt-auto px-2">
             <div className="p-4 rounded-2xl bg-navy-900 border border-navy-700">
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Qualidade Mínima</p>
                <div className="flex items-center gap-1 text-amber-500">
                   {[1,2,3,4,5].map(s => <Star key={s} className={`w-3 h-3 ${s <= (parseInt(formData.rating) || 0) ? 'fill-current' : ''}`} />)}
                </div>
             </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 flex flex-col min-w-0 bg-navy-900">
          <div className="p-6 border-b border-navy-700 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200">
              {tabs.find(t => t.id === activeTab)?.label}
            </h3>
            <button onClick={onClose} className="p-2 rounded-xl hover:bg-navy-800 text-slate-500 transition-all">
              <X className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="flex-1 flex flex-col min-h-0">
            <div className="flex-1 overflow-y-auto p-8 custom-scrollbar space-y-6">
              {activeTab === 'IDENT' && (
                <div className="space-y-6 animate-fadein">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Nome da Oficina*</label>
                      <input name="name" required value={formData.name} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Contato Responsável</label>
                      <input name="contact_name" value={formData.contact_name} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">E-mail Comercial</label>
                      <input name="email" value={formData.email} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">WhatsApp / Telefone</label>
                      <input name="phone" value={formData.phone} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'ADDR' && (
                <div className="space-y-6 animate-fadein">
                   <div className="grid grid-cols-6 gap-6">
                      <div className="col-span-2 space-y-1.5">
                        <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">CEP</label>
                        <input name="zip_code" value={formData.zip_code} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                      </div>
                      <div className="col-span-4 space-y-1.5">
                        <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Endereço Completo</label>
                        <input name="address" value={formData.address} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                      </div>
                      <div className="col-span-3 space-y-1.5">
                        <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Cidade</label>
                        <input name="city" value={formData.city} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                      </div>
                      <div className="col-span-3 space-y-1.5">
                        <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Estado (UF)</label>
                        <input name="state" value={formData.state} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                      </div>
                   </div>
                </div>
              )}

              {activeTab === 'OPER' && (
                <div className="space-y-6 animate-fadein">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Capacidade Simultânea (OS)</label>
                      <input type="number" name="max_concurrent_os" value={formData.max_concurrent_os} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Rating Base (0-5)</label>
                      <input type="number" step="0.1" name="rating" value={formData.rating} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Especialidades (separadas por vírgula)</label>
                    <input name="specialties_csv" value={formData.specialties_csv} onChange={handleChange} placeholder="Ex: Elétrica, Mecânica Pesada, Ar Condicionado" className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Tipos de Ativos (separadas por vírgula)</label>
                    <input name="vehicle_types_csv" value={formData.vehicle_types_csv} onChange={handleChange} placeholder="Ex: SUV, Pickup, Caminhão, Lancha" className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                  </div>
                </div>
              )}

              {activeTab === 'FISCAL' && (
                <div className="space-y-6 animate-fadein">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">CNPJ</label>
                      <input name="cnpj" value={formData.cnpj} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Inscrição Estadual</label>
                      <input name="ie" value={formData.ie} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Vincular ID de Parceiro (User Partner ID)</label>
                    <input type="number" name="partner_id" value={formData.partner_id} onChange={handleChange} placeholder="Opcional: ID do usuário vinculado" className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    <p className="text-[10px] text-slate-500 italic mt-1">Este ID vincula a oficina a um usuário com role PARTNER para acesso ao portal.</p>
                  </div>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-navy-700 bg-navy-800/30 flex items-center justify-between">
              <p className="text-[10px] text-slate-500 font-medium">Campos marcados com * são de preenchimento obrigatório.</p>
              <div className="flex gap-3">
                <button type="button" onClick={onClose} className="px-6 py-2.5 rounded-2xl border border-navy-700 text-slate-400 text-xs font-bold hover:bg-navy-800 transition-all uppercase tracking-widest">
                  Cancelar
                </button>
                <button 
                  type="submit"
                  disabled={loading || !formData.name}
                  className="px-8 py-2.5 rounded-2xl bg-amber-500 text-navy-950 text-xs font-bold hover:bg-amber-400 transition-all shadow-lg shadow-amber-500/20 disabled:opacity-50 flex items-center gap-2 uppercase tracking-widest"
                >
                  {loading ? <Save className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Salvar Oficina
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
