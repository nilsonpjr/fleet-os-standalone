import { FormEvent, useEffect, useState } from 'react'
import { AlertTriangle, X } from 'lucide-react'
import api from '@core/api/client'

type FuelType = 'GASOLINE' | 'ETHANOL' | 'FLEX' | 'DIESEL' | 'ELECTRIC' | 'HYBRID' | 'GNV'
type VehicleCategory = 'CAR' | 'MOTORCYCLE' | 'TRUCK' | 'VAN' | 'BOAT' | 'OTHER'

interface VehicleFormState {
  plate: string
  brand: string
  model: string
  category: VehicleCategory
  fuel_type: FuelType | ''
  renavam: string
  chassis: string
  color: string
  year_model: string
  year_manufacture: string
  mileage_current: string
  ipva_value: string
  ipva_due_date: string
  licensing_year: string
  licensing_due_date: string
  licensing_paid: boolean
  dpvat_value: string
  insurance_policy: string
  insurance_company: string
  insurance_expiry: string
  insurance_value: string
  notes: string
  usage_type: string
  client_id: string
}

const EMPTY_FORM: VehicleFormState = {
  plate: '', brand: '', model: '', category: 'CAR', fuel_type: '',
  renavam: '', chassis: '', color: '', year_model: '', year_manufacture: '',
  mileage_current: '', ipva_value: '', ipva_due_date: '', licensing_year: '',
  licensing_due_date: '', licensing_paid: false, dpvat_value: '',
  insurance_policy: '', insurance_company: '', insurance_expiry: '',
  insurance_value: '', notes: '', usage_type: 'OPERACIONAL', client_id: '',
}

function asNumber(v: string): number | undefined {
  if (!v || !v.trim()) return undefined
  const parsed = Number(v.replace(',', '.'))
  return Number.isFinite(parsed) ? parsed : undefined
}

function asInt(v: string): number | undefined {
  if (!v || !v.trim()) return undefined
  const parsed = parseInt(v, 10)
  return Number.isFinite(parsed) ? parsed : undefined
}

interface CreateVehicleModalProps {
  onClose: () => void
  onSuccess: () => void
  initialData?: any
}

export function CreateVehicleModal({ onClose, onSuccess, initialData }: CreateVehicleModalProps) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'id' | 'fiscal' | 'seguro' | 'operacao' | 'proprietario'>('id')
  const [clients, setClients] = useState<{ id: number; name: string }[]>([])
  
  const [form, setForm] = useState<VehicleFormState>(EMPTY_FORM)

  useEffect(() => {
    // Load clients for the select dropdown
    api.get<{ id: number; name: string }[]>('/api/clients')
       .then(setClients)
       .catch(console.error)
  }, [])

  useEffect(() => {
    if (initialData) {
      setForm({
        plate: initialData.plate || '',
        brand: initialData.brand || '',
        model: initialData.model || '',
        category: initialData.category || 'CAR',
        fuel_type: initialData.fuel_type || '',
        renavam: initialData.renavam || '',
        chassis: initialData.chassis || '',
        color: initialData.color || '',
        year_model: initialData.year_model ? String(initialData.year_model) : '',
        year_manufacture: initialData.year_manufacture ? String(initialData.year_manufacture) : '',
        mileage_current: initialData.mileage_current ? String(initialData.mileage_current) : '',
        ipva_value: initialData.ipva_value ? String(initialData.ipva_value) : '',
        ipva_due_date: initialData.ipva_due_date || '',
        licensing_year: initialData.licensing_year ? String(initialData.licensing_year) : '',
        licensing_due_date: initialData.licensing_due_date || '',
        licensing_paid: initialData.licensing_paid || false,
        dpvat_value: initialData.dpvat_value ? String(initialData.dpvat_value) : '',
        insurance_policy: initialData.insurance_policy || '',
        insurance_company: initialData.insurance_company || '',
        insurance_expiry: initialData.insurance_expiry || '',
        insurance_value: initialData.insurance_value ? String(initialData.insurance_value) : '',
        notes: initialData.notes || '',
        usage_type: initialData.usage_type || 'OPERACIONAL',
        client_id: initialData.client_id ? String(initialData.client_id) : '',
      })
    }
  }, [initialData])

  const createOrUpdateVehicle = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.plate.trim() || !form.brand.trim() || !form.model.trim()) {
      setError('Placa, marca e modelo são obrigatórios.')
      setActiveTab('id')
      return
    }

    setSaving(true)
    setError(null)
    try {
      const payload = {
        plate: form.plate.trim().toUpperCase(),
        brand: form.brand.trim(),
        model: form.model.trim(),
        category: form.category,
        fuel_type: form.fuel_type || undefined,
        renavam: form.renavam || undefined,
        chassis: form.chassis || undefined,
        color: form.color || undefined,
        year_model: asInt(form.year_model),
        year_manufacture: asInt(form.year_manufacture),
        mileage_current: asNumber(form.mileage_current),
        ipva_value: asNumber(form.ipva_value),
        ipva_due_date: form.ipva_due_date || undefined,
        licensing_year: asInt(form.licensing_year),
        licensing_due_date: form.licensing_due_date || undefined,
        licensing_paid: form.licensing_paid,
        dpvat_value: asNumber(form.dpvat_value),
        insurance_policy: form.insurance_policy || undefined,
        insurance_company: form.insurance_company || undefined,
        insurance_expiry: form.insurance_expiry || undefined,
        insurance_value: asNumber(form.insurance_value),
        usage_type: form.usage_type,
        client_id: asInt(form.client_id),
        notes: form.notes || undefined,
      }

      if (initialData?.id) {
        await api.put(`/api/fleet/vehicles/${initialData.id}`, payload)
      } else {
        await api.post('/api/fleet/vehicles', payload)
      }
      onSuccess()
      onClose()
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Falha ao salvar veículo')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl border border-navy-700 bg-navy-900 flex flex-col">
        <div className="bg-navy-900 border-b border-navy-700 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-100">{initialData ? 'Editar Veículo' : 'Novo Veículo'}</h2>
            <p className="text-xs text-slate-400">Complete todas as abas para um controle 360°</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-navy-800 text-slate-400"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex bg-navy-800/50 border-b border-navy-700 px-2 overflow-x-auto no-scrollbar">
          {[
            { id: 'id', label: 'Identificação' },
            { id: 'fiscal', label: 'Fiscal' },
            { id: 'seguro', label: 'Seguro' },
            { id: 'operacao', label: 'Operação' },
            { id: 'proprietario', label: 'Proprietário' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-3 text-xs font-bold uppercase tracking-wider transition-all border-b-2 whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-amber-500 text-amber-500'
                  : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="m-4 px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={createOrUpdateVehicle} className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeTab === 'id' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-in fade-in slide-in-from-bottom-2">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Placa *</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100 focus:ring-1 focus:ring-amber-500" placeholder="AAA-0000" value={form.plate} onChange={(e) => setForm({ ...form, plate: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Marca *</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100 focus:ring-1 focus:ring-amber-500" placeholder="Ex: Honda" value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Modelo *</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100 focus:ring-1 focus:ring-amber-500" placeholder="Ex: Civic" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Categoria</label>
                <select className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value as VehicleCategory })}>
                  <option value="CAR">Carro</option>
                  <option value="MOTORCYCLE">Moto</option>
                  <option value="TRUCK">Caminhão</option>
                  <option value="VAN">Van</option>
                  <option value="OTHER">Outro</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Ano Fabricação</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" placeholder="2023" value={form.year_manufacture} onChange={(e) => setForm({ ...form, year_manufacture: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Ano Modelo</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" placeholder="2024" value={form.year_model} onChange={(e) => setForm({ ...form, year_model: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Cor</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" placeholder="Branco" value={form.color} onChange={(e) => setForm({ ...form, color: e.target.value })} />
              </div>
              <div className="space-y-1.5 lg:col-span-2">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">RENAVAM</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" placeholder="00000000000" value={form.renavam} onChange={(e) => setForm({ ...form, renavam: e.target.value })} />
              </div>
              <div className="space-y-1.5 lg:col-span-2">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Chassi</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" placeholder="Digite o chassi completo" value={form.chassis} onChange={(e) => setForm({ ...form, chassis: e.target.value })} />
              </div>
            </div>
          )}

          {activeTab === 'fiscal' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-in fade-in slide-in-from-bottom-2">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Valor IPVA (R$)</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" placeholder="0,00" value={form.ipva_value} onChange={(e) => setForm({ ...form, ipva_value: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Vencimento IPVA</label>
                <input type="date" className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" value={form.ipva_due_date} onChange={(e) => setForm({ ...form, ipva_due_date: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Ano Licenciamento</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" placeholder="2024" value={form.licensing_year} onChange={(e) => setForm({ ...form, licensing_year: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Vencimento Licenciamento</label>
                <input type="date" className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" value={form.licensing_due_date} onChange={(e) => setForm({ ...form, licensing_due_date: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Valor DPVAT (R$)</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" placeholder="0,00" value={form.dpvat_value} onChange={(e) => setForm({ ...form, dpvat_value: e.target.value })} />
              </div>
              <div className="flex items-center pt-6">
                <label className="inline-flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" className="w-5 h-5 rounded border-navy-700 bg-navy-800 text-amber-500" checked={form.licensing_paid} onChange={(e) => setForm({ ...form, licensing_paid: e.target.checked })} />
                  <span className="text-sm text-slate-300">Licenciamento Pago</span>
                </label>
              </div>
            </div>
          )}

          {activeTab === 'seguro' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in slide-in-from-bottom-2">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Seguradora</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" placeholder="Ex: Porto Seguro" value={form.insurance_company} onChange={(e) => setForm({ ...form, insurance_company: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Nº Apólice</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" placeholder="0000000000" value={form.insurance_policy} onChange={(e) => setForm({ ...form, insurance_policy: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Vigência até</label>
                <input type="date" className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" value={form.insurance_expiry} onChange={(e) => setForm({ ...form, insurance_expiry: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Prêmio/Valor Segurado (R$)</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" placeholder="0,00" value={form.insurance_value} onChange={(e) => setForm({ ...form, insurance_value: e.target.value })} />
              </div>
            </div>
          )}

          {activeTab === 'operacao' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Combustível</label>
                  <select className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" value={form.fuel_type} onChange={(e) => setForm({ ...form, fuel_type: e.target.value as FuelType | '' })}>
                    <option value="">Selecione...</option>
                    <option value="GASOLINE">Gasolina</option>
                    <option value="ETHANOL">Etanol</option>
                    <option value="FLEX">Flex</option>
                    <option value="DIESEL">Diesel</option>
                    <option value="ELECTRIC">Elétrico</option>
                    <option value="HYBRID">Híbrido</option>
                    <option value="GNV">GNV</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">KM Atual</label>
                  <input className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" placeholder="0" value={form.mileage_current} onChange={(e) => setForm({ ...form, mileage_current: e.target.value })} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Tipo de Uso</label>
                  <select className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100" value={form.usage_type} onChange={(e) => setForm({ ...form, usage_type: e.target.value })}>
                    <option value="OPERACIONAL">Operacional</option>
                    <option value="EXECUTIVO">Executivo</option>
                    <option value="FROTA">Frota</option>
                  </select>
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Observações Internas</label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  className="w-full min-h-32 px-4 py-3 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100 resize-none"
                  placeholder="Histórico ou detalhes operacionais importantes..."
                />
              </div>
            </div>
          )}

          {activeTab === 'proprietario' && (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2">
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 flex gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0" />
                <p className="text-xs text-amber-200/80 leading-relaxed">
                  Vincule este veículo a um cliente para permitir que ele visualize a frota em seu portal exclusivo e realize solicitações de serviço.
                </p>
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-slate-500 ml-1">Selecione o Cliente</label>
                <select
                  className="w-full px-4 py-2.5 rounded-xl bg-navy-800 border border-navy-700 text-sm text-slate-100 focus:ring-1 focus:ring-amber-500"
                  value={form.client_id}
                  onChange={(e) => setForm({ ...form, client_id: e.target.value })}
                >
                  <option value="">Nenhum (Uso Interno)</option>
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>{c.name} (ID #{c.id})</option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </form>

        <div className="bg-navy-900 border-t border-navy-700 px-6 py-4 flex justify-between items-center">
          <div className="text-[10px] font-bold uppercase text-slate-600">
            {activeTab === 'proprietario' ? 'Pronto para salvar' : 'Continue preenchendo as abas'}
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2 rounded-xl border border-navy-700 text-slate-300 hover:bg-navy-800 text-sm font-medium transition-all"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={createOrUpdateVehicle}
              disabled={saving}
              className="px-6 py-2 rounded-xl bg-amber-500 text-navy-950 font-bold hover:bg-amber-400 disabled:opacity-60 text-sm transition-all shadow-lg shadow-amber-500/10"
            >
              {saving ? 'Salvando...' : 'Finalizar Cadastro'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
