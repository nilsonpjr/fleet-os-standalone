import { FormEvent, useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Plus, Save, Send, Trash2, Camera, Wrench, Package } from 'lucide-react'
import api from '@core/api/client'
import { useApi } from '@shared/hooks/useApi'
import { FleetRequest, QuoteItem } from '@core/types'
import ChatWidget from '@shared/components/ChatWidget'

export default function QuoteBuilderPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  
  const { data: request, loading, error } = useApi<FleetRequest>(() => 
    api.get(`/api/fleet/requests/${id}`)
  )

  const [diagnosis, setDiagnosis] = useState('')
  const [estimatedDays, setEstimatedDays] = useState('3')
  const [items, setItems] = useState<Partial<QuoteItem>[]>([
    { type: 'LABOR', description: '', quantity: 1, unitPrice: 0, total: 0 }
  ])
  
  const [photos, setPhotos] = useState<File[]>([])
  const [previews, setPreviews] = useState<string[]>([])
  const [sending, setSending] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const totals = useMemo(() => {
    let labor = 0
    let parts = 0
    items.forEach(item => {
      const val = (item.quantity || 0) * (item.unitPrice || 0)
      if (item.type === 'LABOR') labor += val
      else parts += val
    })
    return { labor, parts, total: labor + parts }
  }, [items])

  const addItem = (type: 'PART' | 'LABOR') => {
    setItems([...items, { type, description: '', quantity: 1, unitPrice: 0, total: 0 }])
  }

  const removeItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index))
  }

  const updateItem = (index: number, field: keyof QuoteItem, value: any) => {
    const newItems = [...items]
    const item = { ...newItems[index], [field]: value }
    item.total = (item.quantity || 0) * (item.unitPrice || 0)
    newItems[index] = item
    setItems(newItems)
  }

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files)
      setPhotos(prev => [...prev, ...newFiles])
      const newPreviews = newFiles.map(file => URL.createObjectURL(file))
      setPreviews(prev => [...prev, ...newPreviews])
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!diagnosis.trim()) return setFormError('O diagnóstico é obrigatório.')
    if (items.some(i => !i.description?.trim())) return setFormError('Todos os itens precisam de descrição.')

    setSending(true)
    setFormError(null)

    try {
      // Submit quote
      const quote = await api.post<any>(`/api/fleet/requests/${id}/quotes`, {
        diagnosis,
        estimated_days: parseInt(estimatedDays),
        items: items.map(i => ({
          type: i.type,
          description: i.description,
          quantity: i.quantity,
          unit_price: i.unitPrice,
          total: i.total
        }))
      })

      // Upload photos if any
      if (photos.length > 0) {
        for (const file of photos) {
          const formData = new FormData()
          formData.append('file', file)
          await api.upload(`/api/fleet/quotes/${quote.id}/photos-before`, formData)
        }
      }

      navigate('/workshop/requests')
    } catch (err) {
      setFormError(typeof err === 'string' ? err : 'Erro ao enviar orçamento')
    } finally {
      setSending(false)
    }
  }

  if (loading) return <div className="p-10 text-center text-slate-500">Carregando dados...</div>
  if (error || !request) return <div className="p-10 text-center text-red-400">{error || 'Chamado não encontrado'}</div>

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fadein pb-20">
      <div className="flex items-center gap-4">
        <button 
          onClick={() => navigate('/workshop/requests')}
          className="p-2 rounded-xl bg-navy-800 border border-navy-700 text-slate-400 hover:text-slate-200 transition-all"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Montar Orçamento</h1>
          <p className="text-slate-400 text-sm mt-0.5">Chamado #{request.id} • {request.client?.name}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Diagnosis Section */}
          <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 space-y-4 shadow-xl shadow-black/20">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Wrench className="w-4 h-4" />
              Diagnóstico Técnico
            </h3>
            <textarea
              value={diagnosis}
              onChange={e => setDiagnosis(e.target.value)}
              placeholder="Descreva o que foi identificado após a avaliação inicial..."
              className="w-full min-h-32 px-4 py-3 rounded-xl bg-navy-900 border border-navy-700 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/40 resize-none"
            />
          </div>

          {/* Items Section */}
          <div className="bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden shadow-xl shadow-black/20">
            <div className="px-6 py-4 border-b border-navy-700 flex items-center justify-between bg-navy-900/30">
              <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Itens do Orçamento</h3>
              <div className="flex gap-2">
                <button 
                  onClick={() => addItem('LABOR')}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-blue-500/30 bg-blue-500/10 text-blue-400 text-xs font-bold hover:bg-blue-500/20 transition-all"
                >
                  <Plus className="w-3.5 h-3.5" />
                  + Serviço
                </button>
                <button 
                  onClick={() => addItem('PART')}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-bold hover:bg-emerald-500/20 transition-all"
                >
                  <Plus className="w-3.5 h-3.5" />
                  + Peça
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              {items.map((item, idx) => (
                <div key={idx} className="flex flex-col md:flex-row gap-3 p-4 rounded-xl bg-navy-900 border border-navy-700 group relative">
                  <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-navy-800 border border-navy-700 shrink-0 text-slate-500">
                    {item.type === 'LABOR' ? <Wrench className="w-5 h-5" /> : <Package className="w-5 h-5" />}
                  </div>
                  <div className="flex-1 space-y-3">
                    <input
                      value={item.description}
                      onChange={e => updateItem(idx, 'description', e.target.value)}
                      placeholder={item.type === 'LABOR' ? 'Nome do serviço...' : 'Nome da peça / SKU...'}
                      className="w-full px-3 py-2 rounded-lg bg-navy-800 border border-navy-700 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                    />
                    <div className="grid grid-cols-3 gap-3">
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-600 uppercase">Qtd</label>
                        <input
                          type="number"
                          value={item.quantity}
                          onChange={e => updateItem(idx, 'quantity', parseFloat(e.target.value))}
                          className="w-full px-3 py-1.5 rounded-lg bg-navy-800 border border-navy-700 text-sm text-slate-200"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-600 uppercase">Unitário</label>
                        <input
                          type="number"
                          value={item.unitPrice}
                          onChange={e => updateItem(idx, 'unitPrice', parseFloat(e.target.value))}
                          className="w-full px-3 py-1.5 rounded-lg bg-navy-800 border border-navy-700 text-sm text-slate-200"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-600 uppercase">Total</label>
                        <div className="w-full px-3 py-1.5 rounded-lg bg-navy-800/50 border border-navy-700 text-sm text-slate-400 font-bold">
                          {(item.total || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </div>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => removeItem(idx)}
                    className="md:absolute md:-top-2 md:-right-2 p-1.5 rounded-lg bg-red-500/10 text-red-500 border border-red-500/30 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-500 hover:text-white"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
              
              {items.length === 0 && (
                <div className="text-center py-6 text-slate-500 italic text-sm">
                  Adicione serviços ou peças para compor o orçamento.
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Summary & Submission */}
          <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 space-y-6 shadow-xl shadow-black/20">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Resumo de Valores</h3>
            
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Mão de Obra</span>
                <span className="text-slate-200 font-bold">R$ {totals.labor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Peças</span>
                <span className="text-slate-200 font-bold">R$ {totals.parts.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="pt-3 border-t border-navy-700 flex justify-between items-center">
                <span className="text-slate-100 font-bold">Total Geral</span>
                <span className="text-2xl font-black text-blue-500">R$ {totals.total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold text-slate-500 uppercase">Prazo de Entrega (Dias)</label>
              <input
                type="number"
                value={estimatedDays}
                onChange={e => setEstimatedDays(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-navy-900 border border-navy-700 text-slate-100 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {formError && <div className="text-red-400 text-xs font-bold text-center">{formError}</div>}

            <button
              onClick={handleSubmit}
              disabled={sending}
              className="w-full py-4 rounded-2xl bg-blue-500 text-white font-black hover:bg-blue-400 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20 disabled:opacity-50"
            >
              <Send className="w-5 h-5" />
              {sending ? 'Enviando...' : 'ENVIAR ORÇAMENTO'}
            </button>
          </div>

          {/* Photos Section */}
          <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Camera className="w-4 h-4" />
              Check-in (Entrada)
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {previews.map((src, i) => (
                <div key={i} className="aspect-square rounded-lg border border-navy-700 overflow-hidden">
                  <img src={src} alt="Preview" className="w-full h-full object-cover" />
                </div>
              ))}
              <label className="aspect-square rounded-lg border-2 border-dashed border-navy-700 flex flex-col items-center justify-center text-slate-600 hover:text-blue-500 hover:border-blue-500/50 cursor-pointer transition-all">
                <Plus className="w-5 h-5 mb-1" />
                <span className="text-[10px] font-bold uppercase tracking-wider">Adicionar</span>
                <input type="file" multiple accept="image/*" onChange={handlePhotoChange} className="hidden" />
              </label>
            </div>
          </div>

          {/* Chat Section */}
          <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Dúvidas sobre o serviço?</h3>
            <ChatWidget requestId={Number(id)} />
          </div>
        </div>
      </div>
    </div>
  )
}
