import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Save, Camera, CheckCircle2, ClipboardList, Clock, Wrench, Package, Info } from 'lucide-react'
import { useApi } from '@shared/hooks/useApi'
import api from '@core/api/client'
import PhotoUploadModal from '@shared/components/PhotoUploadModal'
import { TableSkeleton } from '@shared/components/ui'

export default function WorkshopExecutionDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [showPhotoModal, setShowPhotoModal] = useState(false)
  const [saving, setSaving] = useState(false)

  const { data: request, loading, refetch } = useApi<any>(() => 
    api.get(`/api/fleet/requests/${id}`)
  )

  const [notes, setNotes] = useState('')

  if (loading) return <TableSkeleton rows={5} />
  if (!request) return <div className="p-10 text-center">Chamado não encontrado.</div>

  const handleSaveNotes = async () => {
    setSaving(true)
    try {
      await api.put(`/api/fleet/executions/${request.execution?.id}`, {
        technician_notes: notes
      })
      await refetch()
    } catch (err) {
      alert('Erro ao salvar notas')
    } finally {
      setSaving(false)
    }
  }

  const handleUploadPhotos = async (files: File[]) => {
    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        await api.upload(`/api/fleet/requests/${id}/photos`, formData)
      }
      await refetch()
    } catch (err) {
      alert('Erro ao enviar fotos')
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadein pb-20">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button 
          onClick={() => navigate(-1)}
          className="p-3 rounded-2xl bg-navy-900 border border-navy-700 text-slate-400 hover:text-slate-200 transition-all shadow-lg"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
           <h1 className="text-2xl font-bold text-slate-100 uppercase tracking-tighter">
              Execução: Chamado #{request.id}
           </h1>
           <p className="text-slate-400 text-sm font-bold uppercase tracking-widest">{request.vehicle?.plate || request.boat?.name} · {request.client?.name}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          
          {/* Notes Section */}
          <div className="bg-navy-800 border border-navy-700 rounded-3xl p-6 space-y-4 shadow-xl">
            <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <ClipboardList className="w-4 h-4 text-amber-500" />
              Relatório do Técnico
            </h2>
            <textarea
              value={notes || request.execution?.technician_notes || ''}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Descreva o que está sendo feito, peças trocadas ou imprevistos encontrados..."
              className="w-full min-h-40 p-4 rounded-2xl bg-navy-900 border border-navy-700 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/40 resize-none"
            />
            <button 
              onClick={handleSaveNotes}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-navy-700 text-slate-200 font-bold hover:bg-navy-600 transition-all ml-auto disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Salvando...' : 'Salvar Relatório'}
            </button>
          </div>

          {/* Photos/Progress Evidence */}
          <div className="bg-navy-800 border border-navy-700 rounded-3xl p-6 space-y-4 shadow-xl">
             <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <Camera className="w-4 h-4 text-blue-500" />
                  Evidências de Execução
                </h2>
                <button 
                  onClick={() => setShowPhotoModal(true)}
                  className="px-4 py-2 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-bold hover:bg-blue-500/20 transition-all"
                >
                  Adicionar Foto
                </button>
             </div>

             <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {(request.photos || []).map((url: string, i: number) => (
                  <div key={i} className="aspect-video rounded-2xl border border-navy-700 overflow-hidden shadow-lg">
                    <img src={url} className="w-full h-full object-cover hover:scale-105 transition-transform" />
                  </div>
                ))}
                {(request.photos || []).length === 0 && (
                  <div className="col-span-full py-10 text-center bg-navy-900/50 rounded-2xl border-2 border-dashed border-navy-700">
                    <Camera className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                    <p className="text-slate-500 text-xs uppercase font-bold tracking-widest">Sem fotos registradas</p>
                  </div>
                )}
             </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Quick Info / Status */}
          <div className="bg-navy-800 border border-navy-700 rounded-3xl p-6 space-y-6 shadow-xl">
             <div>
                <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">Status do Serviço</h3>
                <div className="flex items-center gap-3">
                   <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                      <Clock className="w-5 h-5 animate-pulse" />
                   </div>
                   <div>
                      <p className="text-lg font-black text-slate-100 uppercase tracking-tighter">Em Execução</p>
                      <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Iniciado em {new Date(request.execution?.started_at).toLocaleDateString('pt-BR')}</p>
                   </div>
                </div>
             </div>

             <div className="pt-6 border-t border-navy-700 space-y-4">
                <div className="flex items-start gap-3">
                   <Info className="w-4 h-4 text-slate-600 mt-0.5" />
                   <p className="text-xs text-slate-500 leading-relaxed italic">
                      Dica: Documente a troca de peças críticas com fotos para facilitar a aprovação final pelo cliente.
                   </p>
                </div>
             </div>

             <button 
               className="w-full py-4 rounded-2xl bg-emerald-500 text-white font-black uppercase tracking-widest shadow-xl shadow-emerald-500/20 active:scale-[0.98] transition-all flex items-center justify-center gap-2"
             >
               <CheckCircle2 className="w-5 h-5" />
               Finalizar Serviço
             </button>
          </div>
        </div>
      </div>

      <PhotoUploadModal 
        isOpen={showPhotoModal}
        onClose={() => setShowPhotoModal(false)}
        onUpload={handleUploadPhotos}
        title="Nova Foto de Progresso"
        subtitle="Evidência técnica da manutenção"
      />
    </div>
  )
}
