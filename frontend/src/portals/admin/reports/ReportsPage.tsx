import { useMemo } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts'
import { TrendingUp, Package, Wrench, DollarSign, Download, Filter, Leaf } from 'lucide-react'
import { useApi } from '@shared/hooks/useApi'
import api from '@core/api/client'
import { KpiCard } from '@shared/components/KpiCard'
import { TableSkeleton } from '@shared/components/ui'

const COLORS = ['#f59e0b', '#0ea5e9', '#10b981', '#ef4444', '#8b5cf6']

export default function ReportsPage() {
  const { data: stats, loading } = useApi<any>(() => api.get('/api/fleet/reports/costs'))
  const { data: vehicles = [] } = useApi<any[]>(() => api.get('/api/fleet/vehicles'))
  const { data: boats = [] } = useApi<any[]>(() => api.get('/api/boats'))
  const { data: orders = [] } = useApi<any[]>(() => api.get('/api/orders'))
  const { data: settings } = useApi<any>(() => api.get('/api/config/settings'))

  const pieData = useMemo(() => {
    if (!stats) return []
    return [
      { name: 'Peças', value: stats.parts_total },
      { name: 'Mão de Obra', value: stats.labor_total },
    ]
  }, [stats])

  const barData = useMemo(() => {
    if (!stats || !stats.by_asset) return []
    
    // Merge names from vehicles/boats
    const assets = [...vehicles, ...boats]
    
    return Object.entries(stats.by_asset)
      .map(([key, value]) => {
        const [type, id] = key.split(':')
        const asset = assets.find(a => a.id === parseInt(id))
        return {
          name: asset?.plate || asset?.name || key,
          value: value
        }
      })
      .sort((a: any, b: any) => b.value - a.value)
      .slice(0, 8) // Top 8
  }, [stats, vehicles, boats])

  const handleExport = (format: 'pdf' | 'csv') => {
    const baseUrl = import.meta.env.VITE_API_URL || '/api'
    window.open(`${baseUrl}/fleet/reports/export/${format}`, '_blank')
  }

  if (loading) return <TableSkeleton rows={5} />

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v)

  return (
    <div className="space-y-6 animate-fadein pb-10">
      <div className="flex items-center justify-between print:hidden">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Relatórios Financeiros</h1>
          <p className="text-slate-400 text-sm mt-0.5">Visão analítica de custos e manutenção da frota.</p>
        </div>
        <div className="flex gap-2 print:hidden">
          <button 
            onClick={() => handleExport('csv')}
            className="px-4 py-2 rounded-xl border border-navy-700 text-slate-400 text-xs font-bold flex items-center gap-2 hover:bg-navy-800 transition-all"
          >
            <Download className="w-3.5 h-3.5" /> Exportar Excel (CSV)
          </button>
          <button 
            onClick={() => window.print()}
            className="px-4 py-2 rounded-xl bg-amber-500 text-navy-950 text-xs font-bold flex items-center gap-2 hover:bg-amber-400 transition-all shadow-lg shadow-amber-500/20"
          >
            <Download className="w-3.5 h-3.5" /> Gerar PDF
          </button>
        </div>
      </div>

      {/* Print-only Header */}
      <div className="hidden print:block mb-8 border-b-2 border-navy-700 pb-4">
         <div className="flex justify-between items-end">
            <div>
               <h1 className="text-3xl font-black text-slate-100">Relatório de Frota · FleetOS</h1>
               <p className="text-slate-400 text-sm">Gerado em {new Date().toLocaleString('pt-BR')}</p>
            </div>
             <div className="text-right">
                <p className="text-xs font-bold text-slate-500 uppercase">{settings?.company_name || settings?.trade_name || 'FleetOS'}</p>
                <p className="text-[10px] text-slate-600">{new Date().toLocaleDateString('pt-BR')}</p>
             </div>
         </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard
          title="Gasto Total"
          value={formatCurrency(stats?.grand_total || 0)}
          subtitle="período selecionado"
          icon={<DollarSign className="w-5 h-5" />}
          accentColor="amber"
        />
        <KpiCard
          title="Ticket Médio OS"
          value={formatCurrency(orders.length > 0 ? (stats?.grand_total || 0) / orders.length : 0)}
          subtitle="custo por intervenção"
          icon={<TrendingUp className="w-5 h-5" />}
          accentColor="sky"
        />
        <KpiCard
          title="Pegada de Carbono"
          value={`${Math.round(stats?.total_co2 || 0).toLocaleString('pt-BR')} kg`}
          subtitle="emissões CO2 estimadas"
          icon={<Leaf className="w-5 h-5" />}
          accentColor="emerald"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost Distribution */}
        <div className="bg-navy-800 border border-navy-700 rounded-3xl p-6">
          <h2 className="text-sm font-bold text-slate-200 mb-6 flex items-center gap-2">
            <Package className="w-4 h-4 text-amber-500" /> Distribuição de Custos
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ background: '#1a2234', border: '1px solid #2d3e5a', borderRadius: 12 }}
                  formatter={(value: any) => formatCurrency(value)}
                />
                <Legend verticalAlign="bottom" height={36}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Assets */}
        <div className="bg-navy-800 border border-navy-700 rounded-3xl p-6">
          <h2 className="text-sm font-bold text-slate-200 mb-6 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-sky-400" /> Top Ativos por Gasto
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} layout="vertical" margin={{ left: 20 }}>
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} width={80} />
                <Tooltip 
                  contentStyle={{ background: '#1a2234', border: '1px solid #2d3e5a', borderRadius: 12 }}
                  formatter={(value: any) => formatCurrency(value)}
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {barData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}
