import { useState } from 'react'
import { User, Users } from 'lucide-react'
import ClientUsersTab from './ClientUsersTab'

export default function ClientProfilePage() {
  const [activeTab, setActiveTab] = useState('users')

  return (
    <div className="space-y-6 animate-fadein pb-10">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Meu Perfil e Acessos</h1>
        <p className="text-slate-400 text-sm mt-0.5">Gerencie os acessos de usuários da sua frota e gerentes.</p>
      </div>

      <div className="flex flex-wrap items-center gap-2 border-b border-navy-700 pb-1">
        <button
          onClick={() => setActiveTab('users')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all ${
            activeTab === 'users' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'text-slate-400 hover:bg-navy-800'
          }`}
        >
          <Users className="w-4 h-4" /> Gestão de Equipe
        </button>
      </div>

      <div className="pt-2">
        {activeTab === 'users' && <ClientUsersTab />}
      </div>
    </div>
  )
}
