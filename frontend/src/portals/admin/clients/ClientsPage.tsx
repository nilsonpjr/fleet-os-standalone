import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, Pencil, Plus, RefreshCw, Save, Search, User, X, LayoutGrid, List as ListIcon, ShieldCheck, ChevronRight } from 'lucide-react'
import api from '@core/api/client'
import { EmptyState, TableSkeleton } from '@shared/components/ui'
import { KpiCard } from '@shared/components/KpiCard'
import ClientFormModal from './ClientFormModal'

interface Client {
  id: number
  name: string
  document: string
  phone?: string | null
  email?: string | null
  address?: string | null
  type?: string | null
  is_active: boolean
}

interface BoatRow { id: number; client_id?: number; clientId?: number }
interface VehicleRow { id: number; client_id?: number | null }

interface ClientDetail {
  id: number
  client_id: number
  company_name?: string | null
  cnpj?: string | null
  contract_type?: string | null
  contract_value?: number | null
}

export default function ClientsPage() {
  const navigate = useNavigate()
  const [clients, setClients] = useState<Client[]>([])
  const [boats, setBoats] = useState<BoatRow[]>([])
  const [vehicles, setVehicles] = useState<VehicleRow[]>([])
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [editingClient, setEditingClient] = useState<any | null>(null)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<'ALL' | 'PF' | 'PJ'>('ALL')
  const [error, setError] = useState<string | null>(null)

  const loadBase = async () => {
    setLoading(true)
    setError(null)
    try {
      const [clientsData, boatsData, vehiclesData] = await Promise.all([
        api.get<Client[]>('/api/clients'),
        api.get<BoatRow[]>('/api/boats').catch(() => []),
        api.get<VehicleRow[]>('/api/fleet/vehicles').catch(() => []),
      ])
      setClients(clientsData)
      setBoats(boatsData)
      setVehicles(vehiclesData)
      if (!selectedClientId && clientsData.length > 0) setSelectedClientId(clientsData[0].id)
    } catch (err) {
      setError('Falha ao carregar clientes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadBase() }, [])

  const countsByClient = useMemo(() => {
    const map = new Map<number, { boats: number; vehicles: number }>()
    clients.forEach(c => map.set(c.id, { boats: 0, vehicles: 0 }))
    boats.forEach(b => {
      const cid = b.clientId ?? b.client_id
      if (cid && map.has(cid)) map.get(cid)!.boats++
    })
    vehicles.forEach(v => {
      if (v.client_id && map.has(v.client_id)) map.get(v.client_id)!.vehicles++
    })
    return map
  }, [clients, boats, vehicles])

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase()
    return clients.filter(c => {
      if (typeFilter !== 'ALL' && (c.type || 'PF') !== typeFilter) return false
      if (!needle) return true
      return c.name.toLowerCase().includes(needle) || c.document.includes(needle)
    })
  }, [clients, search, typeFilter])

  const handleOpenEdit = async (client: Client) => {
    try {
      setLoading(true)
      const detail = await api.get<any>(`/api/fleet/clients/${client.id}/detail`).catch(() => ({}))
      setEditingClient({ ...client, ...detail })
      setShowModal(true)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (formData: any) => {
    setSaving(true)
    try {
      // Split payload into base client and fleet detail
      const basePayload = {
        name: formData.name,
        document: formData.document,
        type: formData.type,
        phone: formData.phone,
        email: formData.email,
        address: formData.address,
      }
      
      const detailPayload = {
        company_name: formData.company_name,
        cnpj: formData.cnpj,
        ie: formData.ie,
        im: formData.im,
        crt: formData.crt,
        billing_address: formData.billing_address,
        billing_city: formData.billing_city,
        billing_state: formData.billing_state,
        billing_zip: formData.billing_zip,
        contract_type: formData.contract_type,
        contract_value: formData.contract_value ? parseFloat(formData.contract_value) : null,
        contract_start: formData.contract_start,
        contract_end: formData.contract_end,
      }

      let clientId = editingClient?.id
      if (editingClient) {
        await api.put(`/api/clients/${editingClient.id}`, basePayload)
      } else {
        const newClient = await api.post<any>('/api/clients', basePayload)
        clientId = newClient.id
      }

      await api.put(`/api/fleet/clients/${clientId}/detail`, detailPayload)
      
      setShowModal(false)
      loadBase()
    } catch (err) {
      setError('Erro ao salvar cadastro completo')
    } finally {
      setSaving(false)
    }
  }

  const activeCount = clients.filter(c => c.is_active).length
  const pjCount = clients.filter(c => (c.type || 'PF') === 'PJ').length

  return (
    <div className="space-y-6 animate-fadein pb-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Gestão de Clientes</h1>
          <p className="text-slate-400 text-sm">Relacionamento, frota vinculada e contratos.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => { setEditingClient(null); setShowModal(true) }} className="px-4 py-2 rounded-xl bg-amber-500 text-navy-950 font-bold flex items-center gap-2 hover:bg-amber-400 transition-all shadow-lg shadow-amber-500/20">
            <Plus className="w-4 h-4" /> Novo Cliente
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard title="Base Ativa" value={activeCount} subtitle="clientes PF/PJ" icon={<User className="w-5 h-5" />} accentColor="amber" loading={loading} />
        <KpiCard title="Contratos PJ" value={pjCount} subtitle="faturamento recorrente" icon={<Building2 className="w-5 h-5" />} accentColor="blue" loading={loading} />
        <KpiCard title="Ativos Gerenciados" value={boats.length + vehicles.length} subtitle="veículos + barcos" icon={<ShieldCheck className="w-5 h-5" />} accentColor="emerald" loading={loading} />
      </div>

      <div className="bg-navy-800 border border-navy-700 rounded-3xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-navy-700 bg-navy-900/50 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-1">
             <div className="relative flex-1 max-w-md">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input 
                  value={search} onChange={e => setSearch(e.target.value)}
                  placeholder="Pesquisar por nome ou documento..."
                  className="w-full pl-10 pr-4 py-2 bg-navy-900 border border-navy-700 rounded-xl text-sm text-slate-200 outline-none focus:border-amber-500/50 transition-all"
                />
             </div>
             <div className="flex p-1 bg-navy-900 rounded-xl border border-navy-700">
               {(['ALL', 'PF', 'PJ'] as const).map(f => (
                 <button key={f} onClick={() => setTypeFilter(f)} className={`px-4 py-1.5 rounded-lg text-[10px] font-bold transition-all ${typeFilter === f ? 'bg-navy-700 text-amber-400 shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}>
                   {f === 'ALL' ? 'TODOS' : f}
                 </button>
               ))}
             </div>
          </div>
          <button onClick={loadBase} className="p-2 rounded-xl border border-navy-700 text-slate-500 hover:bg-navy-700 transition-all">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-navy-700 text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-navy-900/20">
                <th className="px-6 py-4">Cliente</th>
                <th className="px-6 py-4">Documento / Tipo</th>
                <th className="px-6 py-4">Frota Vinculada</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-navy-700">
              {loading ? (
                <tr><td colSpan={5} className="p-10"><TableSkeleton rows={5} /></td></tr>
              ) : filtered.map(c => {
                const cnt = countsByClient.get(c.id) || { boats: 0, vehicles: 0 }
                return (
                  <tr key={c.id} onClick={() => navigate(`/admin/clients/${c.id}`)} className="group hover:bg-navy-700/30 transition-all cursor-pointer">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-navy-900 border border-navy-700 flex items-center justify-center text-amber-500 font-bold">
                          {c.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="text-sm font-bold text-slate-200">{c.name}</p>
                          <p className="text-[10px] text-slate-500">{c.email || 'Sem e-mail'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-xs font-medium text-slate-300">{c.document}</p>
                      <span className={`text-[9px] font-bold px-2 py-0.5 rounded border mt-1 inline-block ${c.type === 'PJ' ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' : 'bg-slate-700/30 border-slate-600 text-slate-400'}`}>
                        {c.type || 'PF'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                       <div className="flex items-center gap-3">
                          <div className="text-center">
                            <p className="text-xs font-bold text-slate-200">{cnt.vehicles}</p>
                            <p className="text-[9px] text-slate-500 uppercase">Carros</p>
                          </div>
                          <div className="w-px h-6 bg-navy-700" />
                          <div className="text-center">
                            <p className="text-xs font-bold text-slate-200">{cnt.boats}</p>
                            <p className="text-[9px] text-slate-500 uppercase">Barcos</p>
                          </div>
                       </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-[10px] font-bold px-2.5 py-1 rounded-lg border flex items-center gap-1.5 w-fit ${c.is_active ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
                        <div className={`w-1.5 h-1.5 rounded-full ${c.is_active ? 'bg-emerald-500' : 'bg-red-500'}`} />
                        {c.is_active ? 'ATIVO' : 'INATIVO'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={(e) => { e.stopPropagation(); handleOpenEdit(c) }} 
                        className="p-2 rounded-lg bg-navy-900 border border-navy-700 text-slate-400 hover:text-amber-500 hover:border-amber-500/50 transition-all"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      <ClientFormModal 
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSave={handleSave}
        initialData={editingClient}
        loading={saving}
      />
    </div>
  )
}
