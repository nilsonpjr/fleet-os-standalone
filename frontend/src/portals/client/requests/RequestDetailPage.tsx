import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Camera, CheckCircle2, Clock, FileText, MapPin, MessageSquare, Wrench, XCircle, ChevronRight, Phone, Send, QrCode, Copy, Check, Car, ShieldCheck } from 'lucide-react'
import api from '@core/api/client'
import { useApi } from '@shared/hooks/useApi'
import { StatusBadge, UrgencyBadge } from '@shared/components/ui'
import ChatWidget from '@shared/components/ChatWidget'
import { FleetRequest, WorkshopQuote } from '@core/types'

function fmtDate(v?: string | null): string {
  if (!v) return '—'
  const dt = new Date(v)
  if (Number.isNaN(dt.getTime())) return v
  return dt.toLocaleDateString('pt-BR')
}

function fmtCurrency(v: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v)
}

export default function RequestDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [approving, setApproving] = useState<number | null>(null)
  
  const { data: request, loading, error, refetch } = useApi<FleetRequest>(() => api.get(`/api/fleet/requests/${id}`))
  const [pixData, setPixData] = useState<{qr_code: string, pix_string: string} | null>(null)
  const [loadingPix, setLoadingPix] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleFetchPix = async () => {
    setLoadingPix(true)
    try {
      const res = await api.get<any>(`/api/transactions/pix/${id}`)
      setPixData(res.data)
    } catch (err) {
      console.error('Erro ao gerar PIX:', err)
    } finally {
      setLoadingPix(false)
    }
  }

  const handleCopyPix = () => {
    if (pixData) {
      navigator.clipboard.writeText(pixData.pix_string)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleApproveQuote = async (quoteId: number) => {
    const confirmed = window.confirm('Deseja aprovar este orçamento e autorizar o serviço?')
    if (!confirmed) return
    setApproving(quoteId)
    try {
      await api.post(`/api/fleet/requests/${id}/approve`, { quote_id: quoteId })
      await refetch()
    } catch (err) {
      alert('Erro ao aprovar orçamento')
    } finally {
      setApproving(null)
    }
  }

  if (loading) return <div className="p-10 text-center text-slate-500 animate-pulse">Carregando detalhes do serviço...</div>
  if (error || !request) return <div className="p-10 text-center text-red-400">{error || 'Solicitação não encontrada'}</div>

  const steps = [
    { label: 'Solicitação Enviada', active: true, done: true, icon: Send },
    { label: 'Em Orçamento', active: request.status !== 'OPEN', done: !['OPEN', 'ASSIGNED'].includes(request.status), icon: FileText },
    { label: 'Aprovação', active: ['ADMIN_APPROVED', 'CLIENT_APPROVED', 'IN_PROGRESS', 'DONE'].includes(request.status), done: ['CLIENT_APPROVED', 'IN_PROGRESS', 'DONE'].includes(request.status), icon: ShieldCheck },
    { label: 'Execução', active: ['IN_PROGRESS', 'DONE'].includes(request.status), done: request.status === 'DONE', icon: Wrench },
    { label: 'Concluído', active: request.status === 'DONE', done: request.status === 'DONE', icon: CheckCircle2 },
  ]

  return (
    <div className="max-w-xl mx-auto space-y-8 animate-fadein pb-32">
      {/* Mobile Header */}
      <div className="flex items-center justify-between bg-navy-900/80 backdrop-blur-xl p-4 -mx-4 border-b border-navy-700 sticky top-0 z-30">
        <button onClick={() => navigate('/client/requests')} className="p-2 rounded-xl bg-navy-800 border border-navy-700 text-slate-400">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <h1 className="text-sm font-black text-slate-100 uppercase tracking-tighter">Chamado #{request.id}</h1>
          <StatusBadge status={request.status} />
        </div>
        <button className="p-2 rounded-xl bg-navy-800 border border-navy-700 text-slate-400">
          <MessageSquare className="w-5 h-5" />
        </button>
      </div>

      {/* Visual Timeline (Premium Vertical) */}
      <div className="bg-navy-900 border border-navy-700 rounded-3xl p-6 relative overflow-hidden shadow-2xl">
         <div className="absolute top-0 right-0 p-4 opacity-10">
            <Clock className="w-20 h-20 text-blue-500" />
         </div>
         <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-6">Linha do Tempo</h2>
         <div className="space-y-8 relative">
            <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-navy-800" />
            {steps.map((step, i) => (
              <div key={i} className="flex gap-6 relative group">
                 <div className={`w-9 h-9 rounded-full border-4 border-navy-900 z-10 flex items-center justify-center transition-all ${
                   step.done ? 'bg-blue-500 shadow-lg shadow-blue-500/20' : step.active ? 'bg-amber-500 animate-pulse' : 'bg-navy-800 text-slate-600'
                 }`}>
                    <step.icon className={`w-4 h-4 ${step.done || step.active ? 'text-white' : ''}`} />
                 </div>
                 <div className="pt-1.5">
                    <p className={`text-sm font-black uppercase tracking-tighter ${step.active ? 'text-slate-100' : 'text-slate-600'}`}>{step.label}</p>
                    {step.active && !step.done && <p className="text-[10px] text-blue-400 font-bold uppercase mt-0.5">Em andamento</p>}
                 </div>
              </div>
            ))}
         </div>
      </div>

      {/* Asset Info */}
      <div className="bg-navy-900 border border-navy-700 rounded-3xl p-6 flex items-center justify-between">
         <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-navy-800 border border-navy-700 flex items-center justify-center text-slate-500">
               <Car className="w-6 h-6" />
            </div>
            <div>
               <p className="text-[10px] font-bold text-slate-500 uppercase">Ativo Vinculado</p>
               <p className="text-sm font-bold text-slate-200">{request.vehicle?.plate || '—'}</p>
            </div>
         </div>
         <ChevronRight className="w-5 h-5 text-slate-700" />
      </div>

      {/* Description & Photos */}
      <div className="bg-navy-900 border border-navy-700 rounded-3xl p-6 space-y-6">
         <div className="space-y-4">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Relato do Cliente</h3>
            <div className="bg-navy-950/50 p-5 rounded-2xl border border-navy-800 text-slate-300 text-sm italic leading-relaxed">
               "{request.problemDescription}"
            </div>
         </div>

         {request.photos && request.photos.length > 0 && (
           <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                 <Camera className="w-4 h-4" /> Evidências Anexadas
              </h3>
              <div className="flex gap-2 overflow-x-auto pb-2 -mx-1 px-1 custom-scrollbar">
                 {request.photos.map((url: string, i: number) => (
                   <div key={i} className="shrink-0 w-32 h-32 rounded-2xl border border-navy-700 overflow-hidden shadow-lg hover:border-blue-500/50 transition-all cursor-pointer">
                      <img src={url} alt={`Evidência ${i}`} className="w-full h-full object-cover" />
                   </div>
                 ))}
              </div>
           </div>
         )}
      </div>

      {/* Orçamentos (Focus) */}
      {request.quotes && request.quotes.length > 0 && (
        <div className="space-y-4">
           <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Orçamentos Recebidos</h3>
           {request.quotes.map((quote: WorkshopQuote) => (
             <div key={quote.id} className="bg-navy-900 border border-navy-700 rounded-3xl overflow-hidden shadow-2xl">
                <div className="p-6 space-y-6">
                   <div className="flex justify-between items-center">
                      <div className="flex items-center gap-3">
                         <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                            <MapPin className="w-5 h-5" />
                         </div>
                         <div>
                            <p className="text-sm font-bold text-slate-100">{quote.workshop?.name}</p>
                            <p className="text-[10px] text-slate-500 uppercase">{quote.estimatedDays} dias úteis</p>
                         </div>
                      </div>
                      <div className="text-right">
                         <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Total</p>
                         <p className="text-xl font-black text-blue-400">{fmtCurrency(quote.totalValue)}</p>
                      </div>
                   </div>

                   <div className="bg-navy-950/50 p-4 rounded-2xl border border-navy-800">
                      <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Diagnóstico da Oficina</p>
                      <p className="text-xs text-slate-400 leading-relaxed italic">"{quote.diagnosis}"</p>
                   </div>

                   {request.status === 'ADMIN_APPROVED' && (
                     <button
                       onClick={() => handleApproveQuote(quote.id)}
                       disabled={approving === quote.id}
                       className="w-full bg-blue-500 py-4 rounded-2xl text-white font-black uppercase tracking-widest shadow-xl shadow-blue-500/20 active:scale-95 transition-all flex items-center justify-center gap-2"
                     >
                       <CheckCircle2 className="w-5 h-5" />
                       {approving === quote.id ? 'Processando...' : 'Aprovar e Iniciar'}
                     </button>
                   )}
                </div>
             </div>
           ))}
        </div>
      )}

      {/* PIX Payment Section (New) */}
      {request.status === 'IN_PROGRESS' && (
        <div className="bg-navy-900 border border-navy-700 rounded-3xl overflow-hidden shadow-2xl p-6 space-y-6">
          <div className="flex items-center gap-3">
             <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <QrCode className="w-5 h-5" />
             </div>
             <div>
                <p className="text-sm font-bold text-slate-100">Pagamento PIX</p>
                <p className="text-[10px] text-slate-500 uppercase">Liberação Imediata</p>
             </div>
          </div>

          {!pixData ? (
            <button 
              onClick={handleFetchPix}
              disabled={loadingPix}
              className="w-full bg-emerald-600/20 border border-emerald-600/30 text-emerald-400 py-4 rounded-2xl font-bold uppercase tracking-widest hover:bg-emerald-600/30 transition-all"
            >
              {loadingPix ? 'Gerando PIX...' : 'Gerar QR Code para Pagamento'}
            </button>
          ) : (
            <div className="space-y-6 text-center animate-fadein">
               <div className="bg-white p-4 rounded-3xl inline-block mx-auto shadow-2xl">
                  <img src={pixData.qr_code} alt="PIX QR Code" className="w-48 h-48" />
               </div>
               
               <div className="space-y-3">
                  <p className="text-xs text-slate-400 px-4">Aponte a câmera do seu banco para o QR Code ou use o botão abaixo para copiar o código.</p>
                  
                  <button 
                    onClick={handleCopyPix}
                    className="w-full flex items-center justify-center gap-2 bg-navy-800 border border-navy-700 py-3 rounded-2xl text-slate-200 text-sm font-semibold hover:bg-navy-700 transition-all"
                  >
                    {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                    {copied ? 'Código Copiado!' : 'Copiar Código PIX'}
                  </button>
               </div>
            </div>
          )}
        </div>
      )}

      {/* Chat Section */}
      <div className="space-y-4">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Mensagens</h3>
        <ChatWidget requestId={Number(id)} />
      </div>

      {/* Support Floating Button */}
      <div className="fixed bottom-28 right-6">
         <button className="w-14 h-14 rounded-full bg-navy-800 border border-navy-700 flex items-center justify-center text-blue-400 shadow-2xl shadow-black/50">
            <Phone className="w-6 h-6" />
         </button>
      </div>
    </div>
  )
}
