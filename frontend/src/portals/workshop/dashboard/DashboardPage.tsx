import { useEffect, useState } from 'react'
import { ClipboardList, CheckSquare, Clock, Wrench, ChevronRight, DollarSign } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@core/auth/store'
import api from '@core/api/client'
import { StatusBadge, UrgencyBadge } from '@shared/components/ui'

export default function WorkshopDashboard() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [requests, setRequests] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<any[]>('/api/fleet/requests/assigned').catch(() => [])
      .then(setRequests)
      .finally(() => setLoading(false))
  }, [])

  const byStatus = (statuses: string[]) =>
    requests.filter(r => statuses.includes(r.status)).length

  return (
    <div className="space-y-6 animate-fadein">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Painel da Oficina</h1>
        <p className="text-slate-400 text-sm mt-0.5">Bem-vindo, {user?.name}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Aguard. Orçamento', count: byStatus(['ASSIGNED']),      icon: <Clock className="w-5 h-5" />,         color: 'text-amber-400', bg: 'bg-amber-500/5' },
          { label: 'Em Execução',        count: byStatus(['IN_PROGRESS']),   icon: <Wrench className="w-5 h-5" />,         color: 'text-emerald-400', bg: 'bg-emerald-500/5' },
          { label: 'Aguard. Retirada',   count: byStatus(['DONE']),          icon: <CheckSquare className="w-5 h-5" />,    color: 'text-sky-400', bg: 'bg-sky-500/5' },
          { label: 'Fat. Estimado',      count: `R$ ${(requests.reduce((acc, r) => acc + (r.quotes?.find((q: any) => q.status === 'APPROVED' || q.status === 'DONE')?.total_value || 0), 0) / 1000).toFixed(1)}k`, icon: <DollarSign className="w-5 h-5" />, color: 'text-blue-400', bg: 'bg-blue-500/5' },
        ].map((s) => (
          <div key={s.label} className={`bg-navy-800 border border-navy-700 rounded-2xl p-5 ${s.bg}`}>
            <div className={`mb-2 ${s.color}`}>{s.icon}</div>
            <div className="text-2xl font-bold text-slate-100">{loading ? '–' : s.count}</div>
            <div className="text-[10px] font-bold text-slate-500 uppercase mt-1 tracking-wider">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Pending list */}
      <div className="bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-navy-700 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <ClipboardList className="w-4 h-4 text-emerald-400" />
            Solicitações Recentes
          </h2>
          <button onClick={() => navigate('/workshop/requests')} className="text-xs text-emerald-400 flex items-center gap-1">
            Ver todas <ChevronRight className="w-3 h-3" />
          </button>
        </div>
        {loading ? (
          <div className="p-4 space-y-3">
            {[1,2,3].map(i => <div key={i} className="h-14 bg-navy-700 rounded-xl animate-pulse" />)}
          </div>
        ) : requests.length === 0 ? (
          <div className="py-12 text-center">
            <ClipboardList className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">Nenhuma solicitação atribuída</p>
            <p className="text-slate-500 text-xs mt-1">Quando a gestora encaminhar uma OS, ela aparecerá aqui</p>
          </div>
        ) : (
          <div className="divide-y divide-navy-700">
            {requests.slice(0,5).map((r) => (
              <div key={r.id} className="px-5 py-3.5 flex items-start gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200 font-medium truncate">{r.problem_description}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {r.vehicle?.plate ?? r.boat?.name ?? '—'} · {new Date(r.created_at).toLocaleDateString('pt-BR')}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-1.5 shrink-0">
                  <StatusBadge status={r.status} />
                  <UrgencyBadge urgency={r.urgency} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
