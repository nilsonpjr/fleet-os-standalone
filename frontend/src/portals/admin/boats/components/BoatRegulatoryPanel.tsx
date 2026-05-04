import { Shield, FileText, CheckCircle, AlertTriangle, Clock } from 'lucide-react'
import { StatusBadge } from '@shared/components/ui'

interface BoatRegulatoryProps {
  data: {
    registration_number?: string
    tmc_expiration?: string
    insurance_expiration?: string
    antf_expiration?: string
    last_inspection_at?: string
  }
}

export function BoatRegulatoryPanel({ data }: BoatRegulatoryProps) {
  const checkStatus = (dateStr?: string) => {
    if (!dateStr) return 'missing'
    const expiry = new Date(dateStr)
    const now = new Date()
    const diff = expiry.getTime() - now.getTime()
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24))

    if (days < 0) return 'expired'
    if (days < 30) return 'warning'
    return 'ok'
  }

  const items = [
    { label: 'TMC (Título de Insc. de Embarcação)', value: data.tmc_expiration, icon: FileText },
    { label: 'Seguro Obrigatório (DPEM)', value: data.insurance_expiration, icon: Shield },
    { label: 'Certificado de Arqueação (ANTF)', value: data.antf_expiration, icon: CheckCircle },
    { label: 'Vistoria Periódica', value: data.last_inspection_at, icon: Clock },
  ]

  return (
    <div className="bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden shadow-xl">
      <div className="p-4 border-b border-navy-700 bg-navy-900/50 flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <Shield className="w-4 h-4 text-sky-400" />
          Status Regulatório
        </h3>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
          Registro: {data.registration_number || 'Não informado'}
        </span>
      </div>

      <div className="p-4 space-y-4">
        {items.map((item, idx) => {
          const status = checkStatus(item.value)
          return (
            <div key={idx} className="flex items-center justify-between group">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${
                  status === 'ok' ? 'bg-emerald-500/10 text-emerald-400' :
                  status === 'warning' ? 'bg-amber-500/10 text-amber-400' :
                  status === 'expired' ? 'bg-red-500/10 text-red-400' :
                  'bg-slate-500/10 text-slate-400'
                }`}>
                  <item.icon className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-200">{item.label}</p>
                  <p className="text-[10px] text-slate-500">
                    {item.value ? `Vence em: ${new Date(item.value).toLocaleDateString()}` : 'Não cadastrado'}
                  </p>
                </div>
              </div>

              {status === 'ok' && <StatusBadge status="CONCLUÍDO" label="OK" />}
              {status === 'warning' && <StatusBadge status="PENDENTE" label="Vencendo" />}
              {status === 'expired' && <StatusBadge status="CANCELADO" label="Vencido" />}
              {status === 'missing' && <StatusBadge status="PENDENTE" label="Faltante" />}
            </div>
          )
        })}
      </div>

      {items.some(i => checkStatus(i.value) === 'expired' || checkStatus(i.value) === 'warning') && (
        <div className="px-4 py-3 bg-red-500/5 border-t border-red-500/10 flex items-center gap-3">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <span className="text-[10px] font-bold text-red-300 uppercase">Atenção: Existem pendências regulatórias críticas</span>
        </div>
      )}
    </div>
  )
}
