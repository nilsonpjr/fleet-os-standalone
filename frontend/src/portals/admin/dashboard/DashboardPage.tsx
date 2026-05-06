import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Car, Ship, ClipboardList, AlertTriangle, CheckCircle,
  Clock, TrendingUp, Bell, ChevronRight, Flame, Gauge, DollarSign, Leaf, Activity
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts'
import { KpiCard } from '@shared/components/KpiCard'
import { StatusBadge, UrgencyBadge, TableSkeleton } from '@shared/components/ui'
import { useAuthStore } from '@core/auth/store'
import api from '@core/api/client'

// ── Types ─────────────────────────────────────────────────
interface DashboardStats {
  totalVehicles: number
  totalBoats: number
  openOrders: number
  pendingQuotes: number
  monthCost: number
  ordersByStatus: { status: string; count: number }[]
  recentOrders: any[]
  totalCo2: number
  categoryCosts: { name: string; value: number }[]
  monthlyHistory: { name: string; value: number }[]
}

interface ExpiryAlert {
  type: 'IPVA' | 'LICENCIAMENTO' | 'SEGURO' | 'DOCUMENTACAO'
  assetName: string
  assetType: 'vehicle' | 'boat'
  dueDate: string
  daysLeft: number
  plate?: string
}

const STATUS_COLORS: Record<string, string> = {
  'Pendente':    '#64748b',
  'Em Orçamento':'#f59e0b',
  'Aprovado':    '#3b82f6',
  'Em Execução': '#0ea5e9',
  'Concluído':   '#10b981',
  'Cancelado':   '#ef4444',
}

// ── Dashboard Page ──────────────────────────────────────────
export default function AdminDashboard() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [alerts, setAlerts] = useState<ExpiryAlert[]>([])
  const [maintAlerts, setMaintAlerts] = useState<any[]>([])
  const [loadingStats, setLoadingStats] = useState(true)
  const [loadingAlerts, setLoadingAlerts] = useState(true)

  useEffect(() => {
    loadStats()
    loadAlerts()
  }, [])

  const loadStats = async () => {
    setLoadingStats(true)
    try {
      const [orders, boats, vehicles] = await Promise.all([
        api.get<any[]>('/api/fleet/requests').catch(() => []),
        api.get<any[]>('/api/fleet/boats').catch(() => []),
        api.get<any[]>('/api/fleet/vehicles').catch(() => []),
      ])

      // Aggregate by status
      const statusCounts: Record<string, number> = {}
      let monthCost = 0
      let totalParts = 0
      let totalLabor = 0
      
      const monthlyData: Record<string, number> = {}
      const now = new Date()
      const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)

      for (const o of orders) {
        statusCounts[o.status] = (statusCounts[o.status] ?? 0) + 1
        
        const orderDate = new Date(o.created_at)
        const monthKey = orderDate.toLocaleDateString('pt-BR', { month: 'short' })
        monthlyData[monthKey] = (monthlyData[monthKey] ?? 0) + (o.total_value ?? 0)

        if (orderDate >= monthStart) {
          monthCost += o.total_value ?? 0
          totalParts += o.subtotal_parts ?? 0
          totalLabor += o.subtotal_labor ?? 0
        }
      }

      const openStatuses = ['OPEN', 'ASSIGNED', 'QUOTED', 'IN_PROGRESS', 'AWAITING_CLOSURE', 'ADMIN_APPROVED', 'CLIENT_APPROVED', 'REVISION_REQUESTED']
      const openOrders = orders.filter((o) => openStatuses.includes(o.status)).length
      const pendingQuotes = orders.filter((o) => o.status === 'QUOTED' || o.status === 'ASSIGNED').length

      // Get last 4 months for history
      const history = Object.entries(monthlyData)
        .slice(-4)
        .map(([name, value]) => ({ name, value }))

      setStats({
        totalVehicles: vehicles.length,
        totalBoats: boats.length,
        openOrders,
        pendingQuotes,
        monthCost,
        ordersByStatus: Object.entries(statusCounts).map(([status, count]) => ({ status, count })),
        recentOrders: orders
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
          .slice(0, 5),
        totalCo2: orders.length * 450,
        categoryCosts: [
          { name: 'Peças', value: totalParts },
          { name: 'Mão de Obra', value: totalLabor }
        ],
        monthlyHistory: history.length > 0 ? history : [{ name: now.toLocaleDateString('pt-BR', { month: 'short' }), value: monthCost }]
      })
    } catch (err) {
      console.error('Dashboard stats error:', err)
    } finally {
      setLoadingStats(false)
    }
  }

  const loadAlerts = async () => {
    setLoadingAlerts(true)
    try {
      const [expiry, maint] = await Promise.all([
        api.get<ExpiryAlert[]>('/api/fleet/alerts').catch(() => []),
        api.get<any[]>('/api/fleet/maintenance/alerts').catch(() => []),
      ])
      setAlerts(expiry)
      setMaintAlerts(maint)
    } finally {
      setLoadingAlerts(false)
    }
  }

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Bom dia'
    if (h < 18) return 'Boa tarde'
    return 'Boa noite'
  }

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v)

  return (
    <div className="space-y-6 animate-fadein">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">
            {greeting()}, {user?.name?.split(' ')[0]} 👋
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            {new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}
          </p>
        </div>
        <button
          onClick={() => { loadStats(); loadAlerts() }}
          className="self-start sm:self-auto px-4 py-2 text-xs font-bold text-slate-400 border border-navy-700 rounded-xl hover:bg-navy-800 transition-all"
        >
          ↻ Atualizar
        </button>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard
          title="Veículos"
          value={loadingStats ? '–' : (stats?.totalVehicles ?? 0)}
          subtitle="ativos na frota"
          icon={<Car className="w-5 h-5" />}
          accentColor="amber"
          loading={loadingStats}
        />
        <KpiCard
          title="OS Abertas"
          value={stats?.openOrders ?? 0}
          subtitle={`${stats?.pendingQuotes} em orçamento`}
          icon={<ClipboardList className="w-5 h-5" />}
          accentColor="sky"
          loading={loadingStats}
        />
        <KpiCard
          title="Preventivas Próximas"
          value={maintAlerts.length}
          subtitle="ativos requerendo atenção"
          icon={<Gauge className="w-5 h-5" />}
          accentColor="amber"
          loading={loadingAlerts}
        />
        <KpiCard
          title="Pegada CO2"
          value={loadingStats ? '–' : `${Math.round(stats?.totalCo2 || 0).toLocaleString()} kg`}
          subtitle="frota eco-friendly"
          icon={<Leaf className="w-5 h-5" />}
          accentColor="emerald"
          loading={loadingStats}
        />
      </div>

      {/* Financial Summary (New Row) */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
         <div className="lg:col-span-1 bg-navy-800 border border-navy-700 rounded-2xl p-5">
            <h2 className="text-sm font-bold text-slate-200 mb-5 flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-emerald-400" />
              Gastos por Categoria
            </h2>
            <div className="h-48 flex items-center justify-center">
               <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={stats?.categoryCosts || [
                        { name: 'Peças', value: 0 },
                        { name: 'Mão de Obra', value: 0 }
                      ]}
                      innerRadius={50}
                      outerRadius={70}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      <Cell fill="#3b82f6" />
                      <Cell fill="#10b981" />
                    </Pie>
                    <Tooltip 
                      formatter={(v: any) => formatCurrency(Number(v))}
                      contentStyle={{ background: '#1a2234', border: '1px solid #2d3e5a', borderRadius: 12 }}
                    />
                  </PieChart>
               </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 mt-2">
               <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
                  <div className="w-2 h-2 rounded-full bg-blue-500" /> Peças
               </div>
               <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
                  <div className="w-2 h-2 rounded-full bg-emerald-500" /> Mão de Obra
               </div>
            </div>
         </div>

         <div className="lg:col-span-3 bg-navy-800 border border-navy-700 rounded-2xl p-5">
            <h2 className="text-sm font-bold text-slate-200 mb-5 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-blue-400" />
              Evolução Mensal de Custos
            </h2>
            <div className="h-48">
               <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats?.monthlyHistory || []}>
                    <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={(v) => `R$ ${v/1000}k`} />
                    <Tooltip 
                      formatter={(v: any) => formatCurrency(Number(v))}
                      contentStyle={{ background: '#1a2234', border: '1px solid #2d3e5a', borderRadius: 12 }}
                    />
                    <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
               </ResponsiveContainer>
            </div>
         </div>
      </div>

      {/* Charts + Alerts row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

        {/* OS by Status chart */}
        <div className="lg:col-span-3 bg-navy-800 border border-navy-700 rounded-2xl p-5">
          <h2 className="text-sm font-bold text-slate-200 mb-5 flex items-center gap-2">
            <ClipboardList className="w-4 h-4 text-amber-400" />
            Ordens de Serviço por Status
          </h2>
          {loadingStats ? (
            <div className="h-48 animate-pulse bg-navy-700 rounded-xl" />
          ) : stats?.ordersByStatus && stats.ordersByStatus.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={stats.ordersByStatus} barCategoryGap="30%">
                <XAxis
                  dataKey="status"
                  tick={{ fill: '#64748b', fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#64748b', fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    background: '#1a2234', border: '1px solid #2d3e5a',
                    borderRadius: 12, color: '#f1f5f9', fontSize: 12,
                  }}
                  cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {stats.ordersByStatus.map((entry) => (
                    <Cell
                      key={entry.status}
                      fill={STATUS_COLORS[entry.status] ?? '#64748b'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-slate-500 text-sm">
              Nenhuma Ordem de Serviço registrada
            </div>
          )}
        </div>

        {/* Expiry Alerts */}
        <div className="lg:col-span-2 bg-navy-800 border border-navy-700 rounded-2xl p-5">
          <h2 className="text-sm font-bold text-slate-200 mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-red-400" />
              Alertas de Vencimento
              {(alerts.length + maintAlerts.length) > 0 && (
                <span className="bg-red-500/20 text-red-400 text-[10px] font-bold px-2 py-0.5 rounded-full border border-red-500/30">
                  {alerts.length + maintAlerts.length}
                </span>
              )}
            </div>
            <button 
              onClick={() => navigate('/admin/alerts')}
              className="text-[10px] font-bold text-red-400 uppercase tracking-widest hover:underline"
            >
              Ver Central
            </button>
          </h2>

          {loadingAlerts ? (
            <div className="space-y-2">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-14 bg-navy-700 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : (alerts.length === 0 && maintAlerts.length === 0) ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <CheckCircle className="w-10 h-10 text-emerald-500/50 mb-2" />
              <p className="text-slate-400 text-sm font-medium">Tudo em dia!</p>
              <p className="text-slate-500 text-xs mt-0.5">Nenhuma pendência crítica identificada</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[300px] overflow-y-auto no-scrollbar pr-1">
              {alerts.map((a, i) => (
                <div key={`exp-${i}`} className="flex items-center gap-3 p-3 rounded-xl bg-navy-900/50 border border-navy-700/50 group hover:border-navy-600 transition-all">
                  <div className={`p-2 rounded-lg ${a.daysLeft <= 5 ? 'bg-red-500/10 text-red-400' : 'bg-amber-500/10 text-amber-400'}`}>
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[10px] font-bold text-slate-500 uppercase">{a.type}</p>
                    <p className="text-xs text-slate-200 font-bold truncate">{a.assetName}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className={`text-[10px] font-bold ${a.daysLeft <= 5 ? 'text-red-400' : 'text-amber-400'} uppercase`}>{a.daysLeft} dias</p>
                    <p className="text-[9px] text-slate-500">{new Date(a.dueDate).toLocaleDateString('pt-BR')}</p>
                  </div>
                </div>
              ))}
              {maintAlerts.map((m, i) => (
                <div key={`maint-${i}`} className="flex items-center gap-3 p-3 rounded-xl bg-sky-500/5 border border-sky-500/20 group hover:border-sky-500/40 transition-all">
                  <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400">
                    <Gauge className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[10px] font-bold text-sky-500 uppercase">PREVENTIVA: {m.service_type}</p>
                    <p className="text-xs text-slate-200 font-bold truncate">{m.asset_name}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-[10px] font-bold text-sky-500 uppercase">ATENÇÃO</p>
                    <p className="text-[9px] text-slate-500 truncate max-w-[60px]">{m.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Orders + Quick Actions row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Recent OS */}
        <div className="lg:col-span-2 bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden">
          <div className="px-5 py-4 border-b border-navy-700 flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Flame className="w-4 h-4 text-amber-400" />
              Ordens Recentes
            </h2>
            <a href="/admin/requests" className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1">
              Ver todas <ChevronRight className="w-3 h-3" />
            </a>
          </div>
          {loadingStats ? (
            <TableSkeleton rows={4} cols={3} />
          ) : (stats?.recentOrders?.length ?? 0) === 0 ? (
            <div className="py-12 text-center text-slate-500 text-sm">
              Nenhuma OS registrada ainda
            </div>
          ) : (
            <div className="divide-y divide-navy-700">
              {stats?.recentOrders.map((o) => (
                <div key={o.id} className="px-5 py-3.5 flex items-center gap-4 hover:bg-navy-700/30 transition-colors">
                  <span className="text-xs font-mono font-bold text-slate-500 w-12 shrink-0">
                    #{String(o.id).padStart(4, '0')}
                  </span>
                  <p className="flex-1 text-sm text-slate-300 truncate">{o.problem_description}</p>
                  <StatusBadge status={o.status} />
                  <span className="text-[10px] text-slate-500 shrink-0">
                    {new Date(o.created_at || o.createdAt).toLocaleDateString('pt-BR')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-navy-800 border border-navy-700 rounded-2xl p-5">
          <h2 className="text-sm font-bold text-slate-200 mb-4">Ações Rápidas</h2>
          <div className="space-y-2">
            {[
              { href: '/admin/vehicles', icon: <Car className="w-4 h-4" />,          label: 'Novo Veículo',          color: 'hover:border-amber-500/40 hover:text-amber-400' },
              { href: '/admin/boats',    icon: <Ship className="w-4 h-4" />,          label: 'Nova Embarcação',        color: 'hover:border-amber-500/40 hover:text-amber-400' },
              { href: '/admin/requests', icon: <ClipboardList className="w-4 h-4" />, label: 'Nova Solicitação',       color: 'hover:border-blue-500/40 hover:text-blue-400' },
              { href: '/admin/workshops',icon: <AlertTriangle className="w-4 h-4" />, label: 'Gerenciar Oficinas',     color: 'hover:border-emerald-500/40 hover:text-emerald-400' },
            ].map((item) => (
              <a
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl border border-navy-700 text-slate-400 text-sm font-medium transition-all ${item.color}`}
              >
                {item.icon}
                {item.label}
                <ChevronRight className="w-3 h-3 ml-auto opacity-50" />
              </a>
            ))}
          </div>
        </div>
      </div>

      {/* Status legend */}
      <div className="flex flex-wrap gap-3 pb-2">
        {Object.entries(STATUS_COLORS).map(([status, color]) => (
          <div key={status} className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
            {status}
          </div>
        ))}
      </div>
    </div>
  )
}
