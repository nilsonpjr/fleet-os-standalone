import { useEffect, useState } from 'react'
import { ClipboardList, Car, Ship, Plus, ChevronRight, Clock } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@core/auth/store'
import api from '@core/api/client'
import { StatusBadge, UrgencyBadge } from '@shared/components/ui'
import AssetCostStats from '@shared/components/AssetCostStats'

export default function ClientDashboard() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [requests, setRequests] = useState<any[]>([])
  const [assets, setAssets] = useState({ vehicles: 0, boats: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const [reqs, boats, vehicles] = await Promise.all([
          api.get<any[]>('/api/fleet/requests/my').catch(() => []),
          api.get<any[]>('/api/boats').catch(() => []),
          api.get<any[]>('/api/fleet/vehicles').catch(() => []),
        ])
        const safeReqs = Array.isArray(reqs) ? reqs : []
        const safeBoats = Array.isArray(boats) ? boats : []
        const safeVehicles = Array.isArray(vehicles) ? vehicles : []
        setRequests(safeReqs.slice(0, 4))
        setAssets({ vehicles: safeVehicles.length, boats: safeBoats.length })
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const pending = requests.filter(r =>
    ['OPEN','ASSIGNED','QUOTED','ADMIN_APPROVED','REVISION_REQUESTED'].includes(r.status)
  ).length

  return (
    <div className="p-4 space-y-5 animate-fadein">
      {/* Greeting */}
      <div className="pt-2">
        <h1 className="text-xl font-bold text-slate-100">
          Olá, {user?.name?.split(' ')[0]} 👋
        </h1>
        <p className="text-slate-400 text-sm mt-0.5">Portal do Cliente · FleetOS</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Veículos', value: assets.vehicles, icon: <Car className="w-5 h-5" />, color: 'text-amber-400' },
          { label: 'Embarcações', value: assets.boats,   icon: <Ship className="w-5 h-5" />,  color: 'text-sky-400' },
          { label: 'Pendentes',   value: pending,         icon: <Clock className="w-5 h-5" />, color: 'text-blue-400' },
        ].map((card) => (
          <div key={card.label} className="bg-navy-800 border border-navy-700 rounded-2xl p-4 text-center">
            <div className={`flex justify-center mb-1 ${card.color}`}>{card.icon}</div>
            <div className="text-2xl font-bold text-slate-100">{loading ? '–' : card.value}</div>
            <div className="text-[10px] text-slate-500 uppercase font-bold">{card.label}</div>
          </div>
        ))}
      </div>

      {/* New Request CTA */}
      <button
        onClick={() => navigate('/client/requests/new')}
        className="w-full flex items-center justify-center gap-3 py-4 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 text-white font-bold rounded-2xl transition-all shadow-lg shadow-blue-500/20"
      >
        <Plus className="w-5 h-5" />
        Abrir Nova Solicitação de Serviço
      </button>

      {/* Stats Overview */}
      <div className="space-y-3">
        <h2 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-2">
           Resumo Financeiro da Frota
        </h2>
        <div className="bg-navy-800/40 border border-navy-700/50 rounded-3xl p-4">
           <AssetCostStats />
        </div>
      </div>

      {/* Recent requests */}
      <div className="bg-navy-800 border border-navy-700 rounded-3xl overflow-hidden shadow-xl">
        <div className="px-4 py-3 border-b border-navy-700 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <ClipboardList className="w-4 h-4 text-blue-400" />
            Minhas Solicitações
          </h2>
          <button onClick={() => navigate('/client/requests')} className="text-xs text-blue-400 flex items-center gap-1">
            Ver todas <ChevronRight className="w-3 h-3" />
          </button>
        </div>

        {loading ? (
          <div className="p-4 space-y-3">
            {[1,2,3].map(i => <div key={i} className="h-14 bg-navy-700 rounded-xl animate-pulse" />)}
          </div>
        ) : requests.length === 0 ? (
          <div className="py-12 text-center">
            <ClipboardList className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <p className="text-slate-400 text-sm">Nenhuma solicitação ainda</p>
            <p className="text-slate-500 text-xs mt-1">Clique no botão acima para abrir sua primeira</p>
          </div>
        ) : (
          <div className="divide-y divide-navy-700">
            {requests.map((r) => (
              <button
                key={r.id}
                onClick={() => navigate(`/client/requests/${r.id}`)}
                className="w-full px-4 py-3.5 flex items-start gap-3 hover:bg-navy-700/40 transition-colors text-left"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-200 truncate">{r.problem_description}</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">
                    {new Date(r.created_at).toLocaleDateString('pt-BR')}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-1.5 shrink-0">
                  <StatusBadge status={r.status} />
                  <UrgencyBadge urgency={r.urgency} />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
