import { ReactNode } from 'react'

interface EmptyStateProps {
  icon: ReactNode
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 rounded-2xl bg-navy-800 border border-navy-700 flex items-center justify-center mb-4 text-slate-500">
        {icon}
      </div>
      <h3 className="text-slate-300 font-bold mb-1">{title}</h3>
      {description && <p className="text-slate-500 text-sm max-w-xs">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

interface TableSkeletonProps { rows?: number; cols?: number }

export function TableSkeleton({ rows = 5, cols = 4 }: TableSkeletonProps) {
  return (
    <div className="animate-pulse space-y-2 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {Array.from({ length: cols }).map((__, j) => (
            <div key={j} className="h-4 bg-navy-700 rounded flex-1" style={{ opacity: 1 - i * 0.12 }} />
          ))}
        </div>
      ))}
    </div>
  )
}

interface StatusBadgeProps {
  status: string
  label?: string
  map?: Record<string, string>
}

const DEFAULT_MAP: Record<string, string> = {
  'OPEN':              'status-open',
  'ASSIGNED':          'status-assigned',
  'QUOTED':            'status-quoted',
  'ADMIN_APPROVED':    'status-quoted',
  'CLIENT_APPROVED':   'status-approved',
  'REVISION_REQUESTED':'status-revision',
  'IN_PROGRESS':       'status-in-progress',
  'AWAITING_CLOSURE':  'status-in-progress',
  'DONE':              'status-done',
  'CANCELED':          'status-canceled',
  // Legacy OS statuses
  'Pendente':       'status-open',
  'Em Orçamento':   'status-quoted',
  'Aprovado':       'status-approved',
  'Em Execução':    'status-in-progress',
  'Concluído':      'status-done',
  'Cancelado':      'status-canceled',
}

const DEFAULT_LABELS: Record<string, string> = {
  'OPEN': 'Aberta',
  'ASSIGNED': 'Encaminhada',
  'QUOTED': 'Orçamento Rec.',
  'ADMIN_APPROVED': 'Aprov. Admin',
  'CLIENT_APPROVED': 'Aprovada',
  'REVISION_REQUESTED': 'Em Revisão',
  'IN_PROGRESS': 'Em Execução',
  'AWAITING_CLOSURE': 'Aguard. Fechamento',
  'DONE': 'Concluída',
  'CANCELED': 'Cancelada',
}

export function StatusBadge({ status, label: customLabel, map = DEFAULT_MAP }: StatusBadgeProps) {
  const cls = map[status] ?? 'status-open'
  const label = customLabel ?? DEFAULT_LABELS[status] ?? status
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border ${cls}`}>
      {label}
    </span>
  )
}

interface UrgencyBadgeProps { urgency: string }

export function UrgencyBadge({ urgency }: UrgencyBadgeProps) {
  const map: Record<string, string> = {
    LOW:      'bg-slate-700/50 text-slate-400 border-slate-600',
    MEDIUM:   'bg-amber-500/15 text-amber-400 border-amber-500/30',
    HIGH:     'bg-orange-500/15 text-orange-400 border-orange-500/30',
    CRITICAL: 'bg-red-500/15 text-red-400 border-red-500/30',
  }
  const labels: Record<string, string> = {
    LOW: 'Baixa', MEDIUM: 'Média', HIGH: 'Alta', CRITICAL: 'Crítica',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${map[urgency] ?? ''}`}>
      {labels[urgency] ?? urgency}
    </span>
  )
}
