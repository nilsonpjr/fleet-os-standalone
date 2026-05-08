import { useState, useEffect } from 'react'
import { X, User, MapPin, Phone, Shield, FileText, Save, Search } from 'lucide-react'

interface ClientFormModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: any) => void
  initialData?: any
  loading?: boolean
}

export default function ClientFormModal({ isOpen, onClose, onSave, initialData, loading }: ClientFormModalProps) {
  const [activeTab, setActiveTab] = useState('IDENT')
  const [formData, setFormData] = useState(initialData || {
    name: '',
    document: '',
    type: 'PF',
    phone: '',
    email: '',
    address: '',
    company_name: '',
    cnpj: '',
    ie: '',
    im: '',
    crt: '1',
    billing_address: '',
    billing_city: '',
    billing_state: '',
    billing_zip: '',
    contract_type: 'MENSAL',
    contract_value: '',
    contract_start: '',
    contract_end: '',
    payment_terms: '',
    account_manager: '',
  })

  useEffect(() => {
    if (initialData) {
      setFormData(initialData)
    } else {
      setFormData({
        name: '', document: '', type: 'PF', phone: '', email: '', address: '',
        company_name: '', cnpj: '', ie: '', im: '', crt: '1',
        billing_address: '', billing_city: '', billing_state: '', billing_zip: '',
        contract_type: 'MENSAL', contract_value: '', contract_start: '', contract_end: '',
        payment_terms: '', account_manager: '',
      })
    }
  }, [initialData])

  if (!isOpen) return null

  const tabs = [
    { id: 'IDENT', label: 'Identificação', icon: User },
    { id: 'ADDR',  label: 'Endereço', icon: MapPin },
    { id: 'CONT',  label: 'Contatos', icon: Phone },
    { id: 'FISCAL', label: 'Dados Fiscais', icon: Shield },
    { id: 'CONTRACT', label: 'Contrato', icon: FileText },
  ]

  const handleChange = (e: any) => {
    const { name, value } = e.target
    setFormData((prev: any) => ({ ...prev, [name]: value }))
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadein">
      <div className="bg-navy-900 border border-navy-700 rounded-3xl w-full max-w-4xl h-[600px] flex overflow-hidden shadow-2xl animate-scalein">
        {/* Sidebar Tabs */}
        <div className="w-64 bg-navy-800/50 border-r border-navy-700 p-4 space-y-2">
          <div className="mb-6 px-2">
            <h2 className="text-lg font-bold text-slate-100">Cadastro de Cliente</h2>
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mt-1">Gestão 360° FleetOS</p>
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
          
          <div className="pt-10 px-2">
             <div className="p-4 rounded-2xl bg-navy-900 border border-navy-700">
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Status do Cadastro</p>
                <div className="flex items-center gap-2">
                   <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                   <span className="text-xs text-slate-300 font-medium">Em Edição</span>
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

          <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
            {activeTab === 'IDENT' && (
              <div className="space-y-6 animate-fadein">
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Nome / Razão Social*</label>
                    <input name="name" value={formData.name} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">CPF / CNPJ*</label>
                    <input name="document" value={formData.document} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Tipo de Cliente</label>
                    <select name="type" value={formData.type} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all appearance-none">
                      <option value="PF">Pessoa Física (PF)</option>
                      <option value="PJ">Pessoa Jurídica (PJ)</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'ADDR' && (
              <div className="space-y-6 animate-fadein">
                 <div className="flex items-center gap-2 text-sky-400 mb-4">
                    <Search className="w-4 h-4" />
                    <span className="text-[10px] font-bold uppercase">Busca automática por CEP disponível</span>
                 </div>
                 <div className="grid grid-cols-6 gap-6">
                    <div className="col-span-2 space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">CEP</label>
                      <input name="billing_zip" value={formData.billing_zip} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                    <div className="col-span-4 space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Endereço Completo</label>
                      <input name="address" value={formData.address} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                 </div>
              </div>
            )}

            {activeTab === 'CONT' && (
              <div className="space-y-6 animate-fadein">
                 <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">E-mail Principal</label>
                      <input name="email" value={formData.email} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Telefone / WhatsApp</label>
                      <input name="phone" value={formData.phone} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                 </div>
              </div>
            )}

            {activeTab === 'FISCAL' && (
              <div className="space-y-6 animate-fadein">
                 <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Razão Social Faturamento</label>
                      <input name="company_name" value={formData.company_name} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">CNPJ Faturamento</label>
                      <input name="cnpj" value={formData.cnpj} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Inscrição Estadual</label>
                      <input name="ie" value={formData.ie} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Regime Tributário (CRT)</label>
                      <select name="crt" value={formData.crt} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all">
                        <option value="1">Simples Nacional</option>
                        <option value="2">Lucro Presumido</option>
                        <option value="3">Lucro Real</option>
                      </select>
                    </div>
                 </div>
              </div>
            )}

            {activeTab === 'CONTRACT' && (
              <div className="space-y-6 animate-fadein">
                 <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Tipo de Contrato</label>
                      <select name="contract_type" value={formData.contract_type} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all">
                        <option value="AVULSO">Avulso / Chamado</option>
                        <option value="MENSAL">Mensalidade Fixa</option>
                        <option value="ANUAL">Plano Anual</option>
                      </select>
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Valor Mensal (R$)</label>
                      <input type="number" name="contract_value" value={formData.contract_value} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Início da Vigência</label>
                      <input type="date" name="contract_start" value={formData.contract_start} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Fim da Vigência</label>
                      <input type="date" name="contract_end" value={formData.contract_end} onChange={handleChange} className="w-full bg-navy-800 border border-navy-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-amber-500 outline-none transition-all" />
                    </div>
                 </div>
              </div>
            )}
          </div>

          <div className="p-6 border-t border-navy-700 bg-navy-800/30 flex items-center justify-between">
            <p className="text-[10px] text-slate-500 font-medium">Campos marcados com * são de preenchimento obrigatório.</p>
            <div className="flex gap-3">
              <button onClick={onClose} className="px-6 py-2.5 rounded-2xl border border-navy-700 text-slate-400 text-xs font-bold hover:bg-navy-800 transition-all">
                Cancelar
              </button>
              <button 
                onClick={() => onSave(formData)}
                disabled={loading || !formData.name || !formData.document}
                className="px-8 py-2.5 rounded-2xl bg-amber-500 text-navy-950 text-xs font-bold hover:bg-amber-400 transition-all shadow-lg shadow-amber-500/20 disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? <Save className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Salvar Cadastro
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
