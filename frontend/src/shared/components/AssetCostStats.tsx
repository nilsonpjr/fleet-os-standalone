import { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { DollarSign, TrendingUp, Package, Wrench } from 'lucide-react'
import { useApi } from '@shared/hooks/useApi'
import api from '@core/api/client'
import { KpiCard } from '@shared/components/KpiCard'

interface AssetCostStatsProps {
  vehicleId?: number
  boatId?: number
}

const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']

export default function AssetCostStats({ vehicleId, boatId }: AssetCostStatsProps) {
  const { data: history = [], loading } = useApi<any[]>(() => {
    const params: any = { status: 'DONE' }
    if (vehicleId) params.vehicle_id = vehicleId
    if (boatId) params.boat_id = boatId
    return api.get('/api/fleet/requests', params)
  })

  const stats = useMemo(() => {
    let total = 0
    let parts = 0
    let labor = 0
    const monthlyData: Record<string, number> = {}

    history.forEach(r => {
      const approved = (r.quotes || []).find((q: any) => q.status === 'APPROVED' || q.status === 'DONE')
      if (approved) {
        const val = approved.total_value || 0
        total += val
        
        // Month aggregation
        const date = new Date(r.created_at)
        const monthKey = date.toLocaleDateString('pt-BR', { month: 'short' })
        monthlyData[monthKey] = (monthlyData[monthKey] || 0) + val

        approved.items?.forEach((i: any) => {
          if (i.type === 'PART') parts += (i.total || 0)
          else labor += (i.total || 0)
        })
      }
    })

    const chartData = Object.entries(monthlyData).map(([name, value]) => ({ name, value }))
    
    return { total, parts, labor, chartData }
  }, [history])

  if (loading) return <div className="h-48 animate-pulse bg-navy-900/50 rounded-2xl" />

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v)

  return (
    <div className="space-y-6 animate-fadein">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard
          title="Total Gasto"
          value={formatCurrency(stats.total)}
          subtitle="histórico acumulado"
          icon={<DollarSign className="w-5 h-5" />}
          accentColor="sky"
        />
        <KpiCard
          title="Mão de Obra"
          value={formatCurrency(stats.labor)}
          subtitle={`${Math.round((stats.labor / (stats.total || 1)) * 100)}% do total`}
          icon={<Wrench className="w-5 h-5" />}
          accentColor="amber"
        />
        <KpiCard
          title="Peças"
          value={formatCurrency(stats.parts)}
          subtitle={`${Math.round((stats.parts / (stats.total || 1)) * 100)}% do total`}
          icon={<Package className="w-5 h-5" />}
          accentColor="emerald"
        />
      </div>

      {stats.chartData.length > 0 && (
        <div className="bg-navy-900/40 border border-navy-700/50 rounded-2xl p-6">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-6 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-sky-400" /> Evolução Mensal de Custos
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.chartData}>
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ background: '#1a2234', border: '1px solid #2d3e5a', borderRadius: 12 }}
                  formatter={(value: any) => formatCurrency(value)}
                  cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {stats.chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}
