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

import { CreateVehicleModal } from './components/CreateVehicleModal'

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
        <CreateVehicleModal 
          onClose={() => setShowCreate(false)}
          onSuccess={load}
        />
      )}
    </div>
  )
}
