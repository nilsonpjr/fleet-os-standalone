import { useEffect, useState } from 'react'
import { Plus, RefreshCw, User, Key, Users } from 'lucide-react'
import api from '@core/api/client'
import { EmptyState, TableSkeleton } from '@shared/components/ui'

interface SystemUser {
  id: number
  name: string
  email: string
  role: string
}

export default function ClientUsersTab() {
  const [users, setUsers] = useState<SystemUser[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [editingUser, setEditingUser] = useState<SystemUser | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  })

  const loadData = async () => {
    setLoading(true)
    try {
      const u = await api.get<SystemUser[]>('/api/auth/users/client')
      setUsers(u)
    } catch (err) {
      setError('Falha ao carregar acessos.')
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
      if (editingUser) {
        const payload: any = {
          name: formData.name,
          email: formData.email,
        }
        if (formData.password) payload.password = formData.password
        await api.put(`/api/auth/users/client/${editingUser.id}`, payload)
      } else {
        await api.post('/api/auth/register/client', formData)
      }
      setShowModal(false)
      loadData()
    } catch (err: any) {
      setError(typeof err === 'string' ? err : 'Erro ao salvar usuário.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (userId: number) => {
    if (!confirm('Tem certeza que deseja remover este acesso da sua frota?')) return
    try {
      await api.delete(`/api/auth/users/client/${userId}`)
      loadData()
    } catch (err: any) {
      setError(typeof err === 'string' ? err : 'Erro ao deletar usuário. Você não pode deletar seu próprio usuário.')
    }
  }

  const openNew = () => {
    setEditingUser(null)
    setFormData({ name: '', email: '', password: '' })
    setShowModal(true)
  }

  const openEdit = (u: SystemUser) => {
    setEditingUser(u)
    setFormData({ name: u.name, email: u.email, password: '' })
    setShowModal(true)
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-400" />
            Membros da Frota
          </h2>
          <p className="text-slate-400 text-sm">Crie logins para que outros gerentes possam acessar o sistema.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadData} className="p-2 rounded-xl border border-navy-700 text-slate-400 hover:text-slate-200 transition-all bg-navy-800">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button onClick={openNew} className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-500 text-white text-sm font-bold rounded-xl hover:bg-blue-400 shadow-lg shadow-blue-500/20 transition-all flex-1 md:flex-none">
            <Plus className="w-4 h-4" /> Novo Membro
          </button>
        </div>
      </div>

      {error && <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-xl">{error}</div>}

      <div className="bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden shadow-xl">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-navy-700 text-[10px] text-slate-500 font-bold uppercase bg-navy-900/40 tracking-widest">
              <th className="px-5 py-3">Usuário</th>
              <th className="px-5 py-3">Nível</th>
              <th className="px-5 py-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-navy-700">
            {loading ? (
              <tr><td colSpan={3} className="p-4"><TableSkeleton rows={3} /></td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={3}><EmptyState icon={<User className="w-8 h-8" />} title="Nenhum usuário extra" description="Crie acessos para sua equipe." /></td></tr>
            ) : (
              users.map(u => (
                <tr key={u.id} className="hover:bg-navy-700/30 transition-all group">
                  <td className="px-5 py-3.5">
                    <p className="text-sm font-bold text-slate-200">{u.name}</p>
                    <p className="text-xs text-slate-500">{u.email}</p>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-lg border border-blue-500/20 bg-blue-500/10 text-blue-400 flex items-center gap-1.5 w-fit uppercase">
                      CLIENTE / GESTOR
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <div className="flex items-center justify-end gap-3 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                      <button onClick={() => openEdit(u)} className="text-xs font-bold text-blue-400 hover:text-blue-300">Editar</button>
                      <button onClick={() => handleDelete(u.id)} className="text-xs font-bold text-red-400 hover:text-red-300">Remover</button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadein">
          <div className="bg-navy-800 border border-navy-700 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-navy-700 bg-navy-900/50">
              <h3 className="text-lg font-bold text-slate-100">
                {editingUser ? 'Editar Acesso' : 'Novo Membro da Frota'}
              </h3>
            </div>
            <form onSubmit={handleSave} className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 mb-1">Nome Completo</label>
                <input required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} placeholder="Ex: Maria Souza" className="w-full px-4 py-2.5 rounded-xl bg-navy-950 border border-navy-700 text-slate-200 text-sm focus:border-blue-500/50 outline-none transition-all" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-400 mb-1">E-mail de Login</label>
                <input type="email" required value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} placeholder="maria@empresa.com.br" className="w-full px-4 py-2.5 rounded-xl bg-navy-950 border border-navy-700 text-slate-200 text-sm focus:border-blue-500/50 outline-none transition-all" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-400 mb-1">
                  {editingUser ? 'Nova Senha (deixe em branco para manter)' : 'Senha Temporária'}
                </label>
                <input type={editingUser ? "password" : "text"} required={!editingUser} value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} placeholder={editingUser ? "••••••••" : "Ex: frota123"} className="w-full px-4 py-2.5 rounded-xl bg-navy-950 border border-navy-700 text-slate-200 text-sm focus:border-blue-500/50 outline-none transition-all" />
              </div>

              <div className="pt-4 flex gap-3 justify-end">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2.5 text-sm font-bold text-slate-400 hover:text-slate-200 transition-all">Cancelar</button>
                <button type="submit" disabled={saving} className="px-5 py-2.5 bg-blue-500 text-white font-bold rounded-xl text-sm hover:bg-blue-400 shadow-lg shadow-blue-500/20 disabled:opacity-50 transition-all">
                  {saving ? 'Salvando...' : 'Salvar Acesso'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
