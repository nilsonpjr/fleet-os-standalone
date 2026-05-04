import { useEffect, useMemo, useState } from 'react'
import { Plus, RefreshCw, Search, Settings2, Star, Users, Wrench } from 'lucide-react'
import api from '@core/api/client'
import { EmptyState, TableSkeleton } from '@shared/components/ui'
import { KpiCard } from '@shared/components/KpiCard'
import WorkshopFormModal from './WorkshopFormModal'

interface Workshop {
  id: number
  name: string
  cnpj?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  city?: string | null
  state?: string | null
  zip_code?: string | null
  contact_name?: string | null
  specialties: string[]
  vehicle_types: string[]
  rating?: number | null
  max_concurrent_os?: number | null
  is_active: boolean
  notes?: string | null
  partner_id?: number | null
}

function toList(csv: string): string[] {
  return csv
    .split(',')
    .map((v) => v.trim())
    .filter(Boolean)
}

function toNumber(v: any): number | undefined {
  if (v === undefined || v === null || v === '') return undefined
  const n = Number(String(v).replace(',', '.'))
  return Number.isFinite(n) ? n : undefined
}

export default function WorkshopsPage() {
  const [workshops, setWorkshops] = useState<Workshop[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<any | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<Workshop[]>('/api/fleet/workshops')
      setWorkshops(data)
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Falha ao carregar oficinas')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase()
    if (!needle) return workshops
    return workshops.filter((w) =>
      w.name.toLowerCase().includes(needle) ||
      (w.city || '').toLowerCase().includes(needle) ||
      (w.specialties || []).join(' ').toLowerCase().includes(needle)
    )
  }, [workshops, search])

  const handleSave = async (formData: any) => {
    setSaving(true)
    setError(null)
    try {
      const payload = {
        name: formData.name.trim(),
        cnpj: formData.cnpj || undefined,
        ie: formData.ie || undefined,
        phone: formData.phone || undefined,
        email: formData.email || undefined,
        address: formData.address || undefined,
        city: formData.city || undefined,
        state: formData.state || undefined,
        zip_code: formData.zip_code || undefined,
        contact_name: formData.contact_name || undefined,
        specialties: toList(formData.specialties_csv),
        vehicle_types: toList(formData.vehicle_types_csv),
        rating: toNumber(formData.rating),
        max_concurrent_os: toNumber(formData.max_concurrent_os),
        notes: formData.notes || undefined,
        partner_id: toNumber(formData.partner_id),
      }
      
      if (editing?.id) {
        await api.put(`/api/fleet/workshops/${editing.id}`, payload)
      } else {
        await api.post('/api/fleet/workshops', payload)
      }
      setShowModal(false)
      load()
    } catch (err) {
      setError('Falha ao salvar oficina')
    } finally {
      setSaving(false)
    }
  }

  const toggleActive = async (w: Workshop) => {
    try {
      await api.put(`/api/fleet/workshops/${w.id}`, { is_active: !w.is_active })
      load()
    } catch (err) {
      setError('Falha ao atualizar status')
    }
  }

  const activeCount = workshops.filter((w) => w.is_active).length
  const avgRating = workshops.length > 0
    ? (workshops.reduce((acc, w) => acc + (w.rating || 0), 0) / workshops.length).toFixed(1)
    : '0.0'

  return (
    <div className="space-y-6 animate-fadein">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Gestão de Oficinas</h1>
          <p className="text-slate-400 text-sm mt-0.5">Rede de parceiros credenciados e capacidade operacional.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => { setEditing(null); setShowModal(true) }} className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500 text-navy-950 font-bold hover:bg-amber-400 transition-all shadow-lg shadow-amber-500/20">
            <Plus className="w-4 h-4" /> Nova Oficina
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard title="Oficinas Ativas" value={activeCount} subtitle="rede disponível" icon={<Wrench className="w-5 h-5" />} accentColor="amber" loading={loading} />
        <KpiCard title="Rating Médio" value={avgRating} subtitle="qualidade percebida" icon={<Star className="w-5 h-5" />} accentColor="blue" loading={loading} />
        <KpiCard title="Capacidade" value={workshops.reduce((acc, w) => acc + (w.max_concurrent_os || 0), 0)} subtitle="OS simultâneas" icon={<Users className="w-5 h-5" />} accentColor="emerald" loading={loading} />
      </div>

      <div className="bg-navy-800 border border-navy-700 rounded-3xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-navy-700 bg-navy-900/50 flex flex-wrap items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar por nome, cidade ou especialidade..." className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-navy-900 border border-navy-700 text-sm text-slate-200 focus:border-amber-500/50 outline-none transition-all" />
          </div>
          <button onClick={load} className="p-2.5 rounded-xl border border-navy-700 text-slate-500 hover:bg-navy-700 transition-all">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {loading ? (
          <TableSkeleton rows={7} cols={6} />
        ) : filtered.length === 0 ? (
          <EmptyState icon={<Wrench className="w-10 h-10" />} title="Nenhuma oficina encontrada" description="Cadastre parceiros para gerenciar ordens de serviço." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-navy-700 text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-navy-900/20">
                  <th className="px-6 py-4">Oficina</th>
                  <th className="px-6 py-4">Contato / Local</th>
                  <th className="px-6 py-4">Especialidades</th>
                  <th className="px-6 py-4">Rating / Cap.</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-700">
                {filtered.map((w) => (
                  <tr key={w.id} className="hover:bg-navy-700/30 transition-all group">
                    <td className="px-6 py-4">
                       <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-navy-900 border border-navy-700 flex items-center justify-center text-amber-500">
                             <Wrench className="w-5 h-5" />
                          </div>
                          <div>
                             <p className="text-sm font-bold text-slate-200">{w.name}</p>
                             <p className="text-[10px] text-slate-500 uppercase font-bold tracking-tight">CNPJ: {w.cnpj || '—'}</p>
                          </div>
                       </div>
                    </td>
                    <td className="px-6 py-4">
                       <p className="text-xs text-slate-300 font-medium">{w.contact_name || '—'}</p>
                       <p className="text-[10px] text-slate-500">{w.city || '—'}/{w.state || '—'}</p>
                    </td>
                    <td className="px-6 py-4">
                       <div className="flex flex-wrap gap-1">
                          {w.specialties.slice(0, 2).map(s => (
                            <span key={s} className="text-[9px] font-bold px-1.5 py-0.5 rounded border border-blue-500/20 bg-blue-500/5 text-blue-400 uppercase">{s}</span>
                          ))}
                          {w.specialties.length > 2 && <span className="text-[9px] font-bold text-slate-600">+{w.specialties.length - 2}</span>}
                       </div>
                    </td>
                    <td className="px-6 py-4">
                       <div className="flex items-center gap-4">
                          <div className="flex items-center gap-1 text-amber-400">
                             <Star className="w-3 h-3 fill-current" />
                             <span className="text-xs font-bold">{(w.rating || 0).toFixed(1)}</span>
                          </div>
                          <div className="flex items-center gap-1 text-slate-500">
                             <Users className="w-3 h-3" />
                             <span className="text-xs font-bold">{w.max_concurrent_os || 0}</span>
                          </div>
                       </div>
                    </td>
                    <td className="px-6 py-4">
                       <span className={`text-[9px] font-bold px-2 py-0.5 rounded-lg border flex items-center gap-1.5 w-fit ${w.is_active ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
                         <div className={`w-1 h-1 rounded-full ${w.is_active ? 'bg-emerald-500' : 'bg-red-500'}`} />
                         {w.is_active ? 'ATIVO' : 'INATIVO'}
                       </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                       <div className="flex justify-end gap-2">
                          <button onClick={() => { setEditing({...w, specialties_csv: (w.specialties || []).join(', '), vehicle_types_csv: (w.vehicle_types || []).join(', ')}); setShowModal(true) }} className="p-2 rounded-lg bg-navy-900 border border-navy-700 text-slate-400 hover:text-blue-400 hover:border-blue-500/50 transition-all">
                             <Settings2 className="w-4 h-4" />
                          </button>
                          <button onClick={() => toggleActive(w)} className={`p-2 rounded-lg bg-navy-900 border border-navy-700 transition-all ${w.is_active ? 'text-red-400 hover:bg-red-500/10' : 'text-emerald-400 hover:bg-emerald-500/10'}`}>
                             <Users className="w-4 h-4" />
                          </button>
                       </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <WorkshopFormModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSave={handleSave}
        initialData={editing}
        loading={saving}
      />
    </div>
  )
}
