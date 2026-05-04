import { FormEvent, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Car, Eye, Plus, RefreshCw, Save, Search, Trash2, X, Leaf } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '@core/api/client'
import { EmptyState, StatusBadge, TableSkeleton, UrgencyBadge } from '@shared/components/ui'
import { KpiCard } from '@shared/components/KpiCard'

type FuelType = 'GASOLINE' | 'ETHANOL' | 'FLEX' | 'DIESEL' | 'ELECTRIC' | 'HYBRID' | 'GNV'
type VehicleCategory = 'CAR' | 'MOTORCYCLE' | 'TRUCK' | 'VAN' | 'BOAT' | 'OTHER'

interface VehicleRow {
  id: number
  client_id: number | null
  plate: string
  brand: string
  model: string
  category: VehicleCategory
  mileage_current: number | null
  fuel_type: FuelType | null
  ipva_due_date: string | null
  licensing_due_date: string | null
  insurance_expiry: string | null
  is_active: boolean
}

interface ExpiryAlert {
  type: 'IPVA' | 'LICENCIAMENTO' | 'SEGURO' | 'DOCUMENTACAO'
  asset_name: string
  asset_type: 'vehicle' | 'boat'
  due_date: string
  days_left: number
  plate?: string
}

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
  plate: '',
  brand: '',
  model: '',
  category: 'CAR',
  fuel_type: '',
  renavam: '',
  chassis: '',
  color: '',
  year_model: '',
  year_manufacture: '',
  mileage_current: '',
  ipva_value: '',
  ipva_due_date: '',
  licensing_year: '',
  licensing_due_date: '',
  licensing_paid: false,
  dpvat_value: '',
  insurance_policy: '',
  insurance_company: '',
  insurance_expiry: '',
  insurance_value: '',
  notes: '',
  usage_type: 'OPERACIONAL',
  client_id: '',
}

function asNumber(v: string): number | undefined {
  if (!v.trim()) return undefined
  const parsed = Number(v.replace(',', '.'))
  return Number.isFinite(parsed) ? parsed : undefined
}

function asInt(v: string): number | undefined {
  if (!v.trim()) return undefined
  const parsed = parseInt(v, 10)
  return Number.isFinite(parsed) ? parsed : undefined
}

function fmtDate(v?: string | null): string {
  if (!v) return '—'
  const dt = new Date(v)
  if (Number.isNaN(dt.getTime())) return v
  return dt.toLocaleDateString('pt-BR')
}

export default function VehiclesPage() {
  const navigate = useNavigate()
  const [vehicles, setVehicles] = useState<VehicleRow[]>([])
  const [clients, setClients] = useState<{ id: number; name: string }[]>([])
  const [alerts, setAlerts] = useState<ExpiryAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [activeTab, setActiveTab] = useState<'id' | 'fiscal' | 'seguro' | 'operacao' | 'proprietario'>('id')
  const [form, setForm] = useState<VehicleFormState>(EMPTY_FORM)
  const [mileageDraft, setMileageDraft] = useState<Record<number, string>>({})

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [vehicleData, alertData, clientData] = await Promise.all([
        api.get<VehicleRow[]>('/api/fleet/vehicles'),
        api.get<ExpiryAlert[]>('/api/fleet/alerts', { days_ahead: 30 }),
        api.get<{ id: number; name: string }[]>('/api/clients'),
      ])
      setVehicles(vehicleData)
      setAlerts(alertData.filter((a) => a.asset_type === 'vehicle'))
      setClients(clientData)
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Falha ao carregar dados')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const clientMap = useMemo(() => {
    const map = new Map<number, string>()
    for (const c of clients) map.set(c.id, c.name)
    return map
  }, [clients])

  const alertCountByPlate = useMemo(() => {
    const map = new Map<string, number>()
    for (const a of alerts) {
      if (!a.plate) continue
      map.set(a.plate, (map.get(a.plate) ?? 0) + 1)
    }
    return map
  }, [alerts])

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase()
    if (!needle) return vehicles
    return vehicles.filter((v) =>
      v.plate.toLowerCase().includes(needle) ||
      v.brand.toLowerCase().includes(needle) ||
      v.model.toLowerCase().includes(needle) ||
      (v.client_id && clientMap.get(v.client_id)?.toLowerCase().includes(needle))
    )
  }, [vehicles, search, clientMap])

  const criticalAlerts = alerts.filter((a) => a.days_left <= 7).length

  const createVehicle = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.plate.trim() || !form.brand.trim() || !form.model.trim()) {
      setError('Placa, marca e modelo são obrigatórios.')
      setActiveTab('id')
      return
    }

    setSaving(true)
    setError(null)
    try {
      await api.post('/api/fleet/vehicles', {
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
      })
      setShowCreate(false)
      setForm(EMPTY_FORM)
      setActiveTab('id')
      await load()
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Falha ao cadastrar veículo')
    } finally {
      setSaving(false)
    }
  }

  const saveMileage = async (vehicle: VehicleRow) => {
    const raw = mileageDraft[vehicle.id]
    if (raw === undefined || raw.trim() === '') return
    const mileage = asNumber(raw)
    if (mileage === undefined) return
    try {
      await api.put(`/api/fleet/vehicles/${vehicle.id}`, { mileage_current: mileage })
      setMileageDraft((prev) => ({ ...prev, [vehicle.id]: '' }))
      await load()
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Falha ao atualizar quilometragem')
    }
  }

  const removeVehicle = async (vehicle: VehicleRow) => {
    const confirmed = window.confirm(`Desativar veículo ${vehicle.plate}?`)
    if (!confirmed) return
    try {
      await api.delete(`/api/fleet/vehicles/${vehicle.id}`)
      await load()
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Falha ao desativar veículo')
    }
  }

  return (
    <div className="space-y-5 animate-fadein">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Veículos</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Cadastro fiscal e operacional da frota automotiva.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={load}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-navy-700 text-slate-300 hover:bg-navy-800 transition-all text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Atualizar
          </button>
          <button
            onClick={() => {
              setForm(EMPTY_FORM)
              setActiveTab('id')
              setShowCreate(true)
            }}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-500 text-navy-950 font-bold hover:bg-amber-400 transition-all text-sm"
          >
            <Plus className="w-4 h-4" />
            Novo Veículo
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard
          title="Veículos Ativos"
          value={vehicles.length}
          subtitle="base atual"
          icon={<Car className="w-5 h-5" />}
          accentColor="amber"
          loading={loading}
        />
        <KpiCard
          title="Alertas (30 dias)"
          value={alerts.length}
          subtitle="IPVA, licenciamento, seguro"
          icon={<AlertTriangle className="w-5 h-5" />}
          accentColor="red"
          loading={loading}
        />
        <KpiCard
          title="Críticos (7 dias)"
          value={criticalAlerts}
          subtitle="prioridade imediata"
          icon={<AlertTriangle className="w-5 h-5" />}
          accentColor="blue"
          loading={loading}
        />
      </div>

      <div className="bg-navy-800 border border-navy-700 rounded-2xl p-4">
        <div className="relative max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Placa, marca, modelo ou proprietário"
            className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-navy-900 border border-navy-700 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
          />
        </div>
      </div>

      {error && (
        <div className="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden">
        {loading ? (
          <TableSkeleton rows={6} cols={6} />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<Car className="w-7 h-7" />}
            title="Nenhum veículo encontrado"
            description="Cadastre veículos para controlar documentação e vencimentos."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-sm">
              <thead className="bg-navy-900/70 border-b border-navy-700">
                <tr className="text-left text-slate-400 text-xs uppercase tracking-wider">
                  <th className="px-4 py-3">Placa</th>
                  <th className="px-4 py-3">Veículo</th>
                  <th className="px-4 py-3">Proprietário</th>
                  <th className="px-4 py-3">Vencimentos</th>
                  <th className="px-4 py-3">Km Atual</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-700">
                {filtered.map((v) => {
                  const alertCount = alertCountByPlate.get(v.plate) ?? 0
                  return (
                    <tr key={v.id} className="hover:bg-navy-700/30">
                      <td className="px-4 py-3">
                        <div className="font-plate text-slate-200 font-semibold">{v.plate}</div>
                        {alertCount > 0 && (
                          <div className="mt-1">
                            <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-bold rounded border border-red-500/30 bg-red-500/10 text-red-400">
                              {alertCount} alerta(s)
                            </span>
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-slate-100 font-medium">{v.brand} {v.model}</div>
                        <div className="text-xs text-slate-500">{v.category} • {v.fuel_type ?? '—'}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-slate-300 font-medium">
                          {v.client_id ? clientMap.get(v.client_id) : '—'}
                        </div>
                        <div className="text-xs text-slate-500">ID #{v.client_id ?? '—'}</div>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-300">
                        <div>IPVA: {fmtDate(v.ipva_due_date)}</div>
                        <div>Lic.: {fmtDate(v.licensing_due_date)}</div>
                        <div>Seguro: {fmtDate(v.insurance_expiry)}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <input
                            value={mileageDraft[v.id] ?? ''}
                            onChange={(e) =>
                              setMileageDraft((prev) => ({ ...prev, [v.id]: e.target.value }))
                            }
                            placeholder={v.mileage_current?.toString() ?? '0'}
                            className="w-20 px-2 py-1.5 rounded-lg bg-navy-900 border border-navy-700 text-slate-200 text-xs"
                          />
                          <button
                            onClick={() => saveMileage(v)}
                            className="p-1.5 rounded-md bg-blue-500/15 text-blue-400 border border-blue-500/30 hover:bg-blue-500/20"
                            title="Salvar quilometragem"
                          >
                            <Save className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        <div className="mt-1 flex items-center gap-1.5 text-[9px] font-bold text-emerald-500/70 uppercase">
                          <Leaf className="w-2.5 h-2.5" />
                          {Math.round((v.mileage_current || 0) * 0.231).toLocaleString()} kg CO2
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => navigate(`/admin/vehicles/${v.id}`)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-navy-700 bg-navy-900 text-slate-400 hover:bg-navy-700 text-xs"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            Detalhes
                          </button>
                          <button
                            onClick={() => removeVehicle(v)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-red-500/30 bg-red-500/10 text-red-300 hover:bg-red-500/20 text-xs"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            Desativar
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl border border-navy-700 bg-navy-900 flex flex-col">
            <div className="bg-navy-900 border-b border-navy-700 px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-100">Novo Veículo</h2>
                <p className="text-xs text-slate-400">Complete todas as abas para um controle 360°</p>
              </div>
              <button
                onClick={() => setShowCreate(false)}
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

            <form onSubmit={createVehicle} className="flex-1 overflow-y-auto p-6 space-y-6">
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
                  onClick={() => setShowCreate(false)}
                  className="px-5 py-2 rounded-xl border border-navy-700 text-slate-300 hover:bg-navy-800 text-sm font-medium transition-all"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={createVehicle}
                  disabled={saving}
                  className="px-6 py-2 rounded-xl bg-amber-500 text-navy-950 font-bold hover:bg-amber-400 disabled:opacity-60 text-sm transition-all shadow-lg shadow-amber-500/10"
                >
                  {saving ? 'Salvando...' : 'Finalizar Cadastro'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
