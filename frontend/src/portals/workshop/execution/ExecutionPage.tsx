import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle2, Clock, Play, Search, Wrench, Camera, ChevronRight } from 'lucide-react'
import api from '@core/api/client'
import { useApi } from '@shared/hooks/useApi'
import { EmptyState, TableSkeleton, StatusBadge } from '@shared/components/ui'
import { FleetRequest } from '@core/types'
import PhotoUploadModal from '@shared/components/PhotoUploadModal'

export default function ExecutionPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [selectedRequest, setSelectedRequest] = useState<number | null>(null)
  
  const { data: requests = [], loading, error, refetch } = useApi<FleetRequest[]>(() => 
    api.get('/api/fleet/requests')
  )

  const activeJobs = useMemo(() => {
    const filtered = requests.filter(r => 
      ['CLIENT_APPROVED', 'IN_PROGRESS', 'AWAITING_CLOSURE'].includes(r.status)
    )
    const needle = search.trim().toLowerCase()
    if (!needle) return filtered
    return filtered.filter(r => 
      r.client?.name.toLowerCase().includes(needle) ||
      r.vehicle?.plate.toLowerCase().includes(needle)
    )
  }, [requests, search])

  const handleStart = async (requestId: number) => {
    try {
      await api.patch(`/api/fleet/requests/${requestId}`, { status: 'IN_PROGRESS' })
      refetch()
    } catch (err) {
      alert('Erro ao iniciar serviço')
    }
  }

  const handleUploadProgress = async (files: File[]) => {
    if (!selectedRequest) return
    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        // Note: The endpoint depends on whether it's before or during/after. 
        // For progress, we'll use a generic photos-after or similar if available, 
        // or just add to the request's photo list.
        await api.upload(`/api/fleet/requests/${selectedRequest}/photos`, formData)
      }
      refetch()
    } catch (err) {
      alert('Erro ao enviar fotos de progresso')
    }
  }

  const handleFinish = async (requestId: number) => {
    const confirmed = window.confirm('Confirmar finalização do serviço?')
    if (!confirmed) return
    try {
      await api.patch(`/api/fleet/requests/${requestId}`, { status: 'DONE' })
      refetch()
    } catch (err) {
      alert('Erro ao finalizar serviço')
    }
  }

  return (
    <div className="space-y-6 animate-fadein pb-10">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Fila de Execução</h1>
        <p className="text-slate-400 text-sm mt-0.5">Gerencie os serviços ativos e reporte o progresso.</p>
      </div>

      <div className="bg-navy-800 border border-navy-700 rounded-2xl p-4 flex items-center justify-between">
        <div className="relative max-w-md w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por placa ou cliente..."
            className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-navy-900 border border-navy-700 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
          />
        </div>
      </div>

      {loading ? (
        <TableSkeleton rows={4} />
      ) : activeJobs.length === 0 ? (
        <EmptyState
          icon={<Play className="w-10 h-10" />}
          title="Nenhum serviço em execução"
          description="Aguardando aprovação de clientes para iniciar novos serviços."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {activeJobs.map((r) => (
            <div key={r.id} className="bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden shadow-lg shadow-black/10">
              <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex gap-4">
                  <div className={`w-14 h-14 rounded-2xl border flex items-center justify-center shrink-0 ${
                    r.status === 'IN_PROGRESS' ? 'bg-blue-500/10 border-blue-500/30 text-blue-500' : 'bg-navy-900 border-navy-700 text-slate-600'
                  }`}>
                    {r.status === 'IN_PROGRESS' ? <Clock className="w-7 h-7 animate-pulse" /> : <Wrench className="w-7 h-7" />}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-slate-100">Chamado #{r.id}</span>
                      <StatusBadge status={r.status} />
                    </div>
                    <div className="text-sm text-slate-300 font-medium">
                      {r.vehicle?.plate} — {r.client?.name}
                    </div>
                    <div className="text-xs text-slate-500 line-clamp-1">
                      {r.problemDescription}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {r.status === 'CLIENT_APPROVED' && (
                    <button 
                      onClick={() => handleStart(r.id)}
                      className="px-6 py-2.5 rounded-xl bg-blue-500 text-white font-bold hover:bg-blue-400 transition-all flex items-center gap-2"
                    >
                      <Play className="w-4 h-4 fill-current" />
                      Iniciar Serviço
                    </button>
                  )}
                  {r.status === 'IN_PROGRESS' && (
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => navigate(`/workshop/execution/${r.id}`)}
                        className="p-2.5 rounded-xl bg-navy-900 border border-navy-700 text-slate-400 hover:text-slate-200 transition-all"
                        title="Ver Detalhes da Execução"
                      >
                        <ChevronRight className="w-5 h-5" />
                      </button>
                      <button 
                        onClick={() => setSelectedRequest(r.id)}
                        className="p-2.5 rounded-xl bg-navy-900 border border-navy-700 text-slate-400 hover:text-blue-400 transition-all"
                        title="Anexar Fotos do Progresso"
                      >
                        <Camera className="w-5 h-5" />
                      </button>
                      <button 
                        onClick={() => handleFinish(r.id)}
                        className="px-6 py-2.5 rounded-xl bg-emerald-500 text-white font-bold hover:bg-emerald-400 transition-all flex items-center gap-2 shadow-lg shadow-emerald-500/10"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        Finalizar
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Progress Detail */}
              {r.status === 'IN_PROGRESS' && (
                <div className="px-5 py-3 bg-navy-900/50 border-t border-navy-700 flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                    Cronômetro Ativo: 02h 45m
                  </div>
                  <div className="flex items-center gap-4">
                    <span>Mecânico: João Silva</span>
                    <button className="text-blue-500 hover:underline">Ver Peças →</button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <PhotoUploadModal 
        isOpen={!!selectedRequest}
        onClose={() => setSelectedRequest(null)}
        onUpload={handleUploadProgress}
        title="Fotos de Progresso"
        subtitle={`Reportando evolução para o Chamado #${selectedRequest}`}
      />
    </div>
  )
}
