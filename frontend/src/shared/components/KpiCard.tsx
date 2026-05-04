import { ReactNode } from 'react'

interface KpiCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: ReactNode
  accentColor: 'amber' | 'blue' | 'emerald' | 'red' | 'sky'
  trend?: { value: number; label: string }
  loading?: boolean
}

const colorMap = {
  amber:   { bg: 'bg-amber-500/10',   border: 'border-amber-500/20',   icon: 'text-amber-400',   val: 'text-amber-400' },
  blue:    { bg: 'bg-blue-500/10',    border: 'border-blue-500/20',    icon: 'text-blue-400',    val: 'text-blue-400' },
  emerald: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', icon: 'text-emerald-400', val: 'text-emerald-400' },
  red:     { bg: 'bg-red-500/10',     border: 'border-red-500/20',     icon: 'text-red-400',     val: 'text-red-400' },
  sky:     { bg: 'bg-sky-500/10',     border: 'border-sky-500/20',     icon: 'text-sky-400',     val: 'text-sky-400' },
}

export function KpiCard({ title, value, subtitle, icon, accentColor, trend, loading }: KpiCardProps) {
  const c = colorMap[accentColor]

  if (loading) {
    return (
      <div className="bg-navy-800 border border-navy-700 rounded-2xl p-5 animate-pulse">
        <div className="h-3 bg-navy-700 rounded w-2/3 mb-4" />
        <div className="h-8 bg-navy-700 rounded w-1/2 mb-2" />
        <div className="h-3 bg-navy-700 rounded w-1/3" />
      </div>
    )
  }

  return (
    <div className={`bg-navy-800 border border-navy-700 rounded-2xl p-5 hover:border-navy-600 transition-all group`}>
      <div className="flex items-start justify-between mb-4">
        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">{title}</p>
        <div className={`p-2 rounded-xl ${c.bg} border ${c.border}`}>
          <span className={c.icon}>{icon}</span>
        </div>
      </div>

      <div className={`text-3xl font-bold ${c.val} mb-1`}>{value}</div>

      {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}

      {trend && (
        <div className="mt-3 flex items-center gap-1.5">
          <span className={`text-xs font-bold ${trend.value >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}%
          </span>
          <span className="text-xs text-slate-500">{trend.label}</span>
        </div>
      )}
    </div>
  )
}
