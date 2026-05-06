import { useEffect, useState } from 'react'
import { CheckCircle2, Plus, RefreshCw, ShieldAlert, User, Key, Building, Wrench } from 'lucide-react'
import api from '@core/api/client'
import { EmptyState, TableSkeleton } from '@shared/components/ui'

interface SystemUser {
  id: number
  name: string
  email: string
  role: string
  client_id?: number
  partner_id?: number
}

interface Client {
  id: number
  name: string
}

interface Workshop {
  id: number
  name: string
}

export default function UsersTab() {
  const [users, setUsers] = useState<SystemUser[]>([])
  const [clients, setClients] = useState<Client[]>([])
  const [workshops, setWorkshops] = useState<Workshop[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'TECHNICIAN',
    client_id: '',
    partner_id: '',
  })

  const loadData = async () => {
    setLoading(true)
    try {
      const [u, c, w] = await Promise.all([
        api.get<SystemUser[]>('/api/auth/users'),
        api.get<Client[]>('/api/clients'),
        api.get<Workshop[]>('/api/fleet/workshops')
      ])
      setUsers(u)
      setClients(c)
      setWorkshops(w)
    } catch (err) {
      setError('Falha ao carregar dados.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const payload: any = {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        role: formData.role,
      }
      if (formData.role === 'CLIENT' && formData.client_id) {
        payload.client_id = Number(formData.client_id)
      }
      if (formData.role === 'PARTNER' && formData.partner_id) {
        payload.partner_id = Number(formData.partner_id)
      }

      await api.post('/api/auth/register', payload)
      setShowModal(false)
      setFormData({ name: '', email: '', password: '', role: 'TECHNICIAN', client_id: '', partner_id: '' })
      loadData()
    } catch (err: any) {
      setError(typeof err === 'string' ? err : 'Erro ao criar usuário.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (userId: number) => {
    if (!confirm('Tem certeza que deseja remover este acesso?')) return
    try {
      await api.delete(`/api/auth/users/${userId}`)
      loadData()
    } catch (err: any) {
      setError(typeof err === 'string' ? err : 'Erro ao deletar usuário.')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Key className="w-5 h-5 text-amber-400" />
            Gestão de Acessos
          </h2>
          <p className="text-slate-400 text-sm">Vincule logins de Clientes e Oficinas (Gestora - CRM).</p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadData} className="p-2 rounded-xl border border-navy-700 text-slate-400 hover:text-slate-200">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button onClick={() => setShowModal(true)} className="flex items-center gap-2 px-3 py-2 bg-amber-500 text-navy-950 text-sm font-bold rounded-xl hover:bg-amber-400">
            <Plus className="w-4 h-4" /> Novo Acesso
          </button>
        </div>
      </div>

      {error && <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-xl">{error}</div>}

      <div className="bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-navy-700 text-[10px] text-slate-500 font-bold uppercase bg-navy-900/40">
              <th className="px-4 py-3">Usuário</th>
              <th className="px-4 py-3">Nível de Acesso</th>
              <th className="px-4 py-3">Vinculação (Cliente/Oficina)</th>
              <th className="px-4 py-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-navy-700">
            {loading ? (
              <tr><td colSpan={4} className="p-4"><TableSkeleton rows={4} /></td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={4}><EmptyState icon={<User className="w-8 h-8" />} title="Nenhum usuário" description="Nenhum acesso cadastrado." /></td></tr>
            ) : (
              users.map(u => (
                <tr key={u.id} className="hover:bg-navy-700/20">
                  <td className="px-4 py-3">
                    <p className="text-sm font-bold text-slate-200">{u.name}</p>
                    <p className="text-xs text-slate-500">{u.email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs font-bold px-2 py-1 rounded bg-navy-900 border border-navy-700 text-amber-400">
                      {u.role}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {u.role === 'CLIENT' && (
                      <div className="flex items-center gap-1.5 text-xs text-blue-400">
                        <Building className="w-3 h-3" />
                        {clients.find(c => c.id === u.client_id)?.name || `ID ${u.client_id}`}
                      </div>
                    )}
                    {u.role === 'PARTNER' && (
                      <div className="flex items-center gap-1.5 text-xs text-emerald-400">
                        <Wrench className="w-3 h-3" />
                        {workshops.find(w => w.id === u.partner_id)?.name || `ID ${u.partner_id}`}
                      </div>
                    )}
                    {u.role !== 'CLIENT' && u.role !== 'PARTNER' && (
                      <span className="text-xs text-slate-500">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => handleDelete(u.id)} className="text-xs text-red-400 hover:underline">Remover</button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-navy-800 border border-navy-700 rounded-2xl w-full max-w-md overflow-hidden">
            <div className="p-4 border-b border-navy-700">
              <h3 className="text-lg font-bold text-slate-100">Novo Acesso (Login)</h3>
            </div>
            <form onSubmit={handleSave} className="p-4 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 mb-1">Nome</label>
                <input required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full px-3 py-2 rounded-xl bg-navy-900 border border-navy-700 text-slate-200 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-400 mb-1">E-mail</label>
                <input type="email" required value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} className="w-full px-3 py-2 rounded-xl bg-navy-900 border border-navy-700 text-slate-200 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-400 mb-1">Senha Temporária</label>
                <input type="password" required value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} className="w-full px-3 py-2 rounded-xl bg-navy-900 border border-navy-700 text-slate-200 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-400 mb-1">Nível de Acesso (Role)</label>
                <select value={formData.role} onChange={e => setFormData({...formData, role: e.target.value, client_id: '', partner_id: ''})} className="w-full px-3 py-2 rounded-xl bg-navy-900 border border-navy-700 text-slate-200 text-sm">
                  <option value="ADMIN">Administrador (Gestora)</option>
                  <option value="MANAGER">Gerente</option>
                  <option value="TECHNICIAN">Técnico Interno</option>
                  <option value="CLIENT">Cliente (Dono de Frota)</option>
                  <option value="PARTNER">Oficina Parceira</option>
                </select>
              </div>

              {formData.role === 'CLIENT' && (
                <div>
                  <label className="block text-xs font-bold text-slate-400 mb-1">Vincular Cadastro de Cliente</label>
                  <select required value={formData.client_id} onChange={e => setFormData({...formData, client_id: e.target.value})} className="w-full px-3 py-2 rounded-xl bg-navy-900 border border-navy-700 text-slate-200 text-sm">
                    <option value="">Selecione o Cliente...</option>
                    {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
              )}

              {formData.role === 'PARTNER' && (
                <div>
                  <label className="block text-xs font-bold text-slate-400 mb-1">Vincular Cadastro de Oficina</label>
                  <select required value={formData.partner_id} onChange={e => setFormData({...formData, partner_id: e.target.value})} className="w-full px-3 py-2 rounded-xl bg-navy-900 border border-navy-700 text-slate-200 text-sm">
                    <option value="">Selecione a Oficina...</option>
                    {workshops.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
                  </select>
                </div>
              )}

              <div className="pt-4 flex gap-2 justify-end">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200">Cancelar</button>
                <button type="submit" disabled={saving} className="px-4 py-2 bg-amber-500 text-navy-950 font-bold rounded-xl text-sm hover:bg-amber-400 disabled:opacity-50">
                  {saving ? 'Criando...' : 'Criar Acesso'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
