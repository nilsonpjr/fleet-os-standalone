import { useState } from 'react'
import { Settings2, Users } from 'lucide-react'
import WorkshopUsersTab from './WorkshopUsersTab'

export default function WorkshopSettingsPage() {
  const [activeTab, setActiveTab] = useState('users')

  return (
    <div className="space-y-6 animate-fadein">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Configurações da Oficina</h1>
        <p className="text-slate-400 text-sm mt-0.5">Gerencie os acessos dos seus mecânicos e preferências.</p>
      </div>

      <div className="flex flex-wrap items-center gap-2 border-b border-navy-700 pb-1">
        <button
          onClick={() => setActiveTab('users')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all ${
            activeTab === 'users' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'text-slate-400 hover:bg-navy-800'
          }`}
        >
          <Users className="w-4 h-4" /> Gestão de Acessos
        </button>
      </div>

      <div className="pt-2">
        {activeTab === 'users' && <WorkshopUsersTab />}
      </div>
    </div>
  )
}
