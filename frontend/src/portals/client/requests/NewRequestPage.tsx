import { FormEvent, useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, Camera, Car, Send, Ship, AlertTriangle, Clock, ShieldCheck, X } from 'lucide-react'
import api from '@core/api/client'
import { useApi } from '@shared/hooks/useApi'
import { Vehicle } from '@core/types'

export default function NewRequestPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const initialId = searchParams.get('id')
  const initialType = searchParams.get('type')

  const { data: vehicles = [], loading: loadingVehicles } = useApi<Vehicle[]>(() => api.get('/api/fleet/vehicles'))
  const { data: boats = [], loading: loadingBoats } = useApi<any[]>(() => api.get('/api/boats'))

  const [form, setForm] = useState({
    assetId: initialId && initialType ? `${initialType}:${initialId}` : '',
    urgency: 'MEDIUM',
    problemDescription: '',
    preferredDate: '',
  })
  
  const [photos, setPhotos] = useState<File[]>([])
  const [previews, setPreviews] = useState<string[]>([])
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files)
      setPhotos(prev => [...prev, ...newFiles])
      const newPreviews = newFiles.map(file => URL.createObjectURL(file))
      setPreviews(prev => [...prev, ...newPreviews])
    }
  }

  const removePhoto = (index: number) => {
    setPhotos(prev => prev.filter((_, i) => i !== index))
    setPreviews(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.assetId) return setError('Selecione um ativo.')
    if (!form.problemDescription.trim()) return setError('Descreva o problema.')

    setSending(true)
    setError(null)

    try {
      const [type, id] = form.assetId.split(':')
      const request = await api.post<any>('/api/fleet/requests', {
        vehicle_id: type === 'VEHICLE' ? parseInt(id) : undefined,
        boat_id: type === 'BOAT' ? parseInt(id) : undefined,
        urgency: form.urgency,
        problem_description: form.problemDescription,
        preferred_date: form.preferredDate || undefined,
      })

      if (photos.length > 0) {
        for (const file of photos) {
          const formData = new FormData()
          formData.append('file', file)
          await api.upload(`/api/fleet/requests/${request.id}/photos`, formData)
        }
      }
      navigate('/client/requests')
    } catch (err) {
      setError('Falha ao enviar solicitação')
    } finally {
      setSending(false)
    }
  }

  const urgencyOptions = [
    { id: 'LOW', label: 'Rotina', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { id: 'MEDIUM', label: 'Necessário', color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { id: 'HIGH', label: 'Urgente', color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { id: 'CRITICAL', label: 'Emergência', color: 'text-red-400', bg: 'bg-red-500/10' },
  ]

  return (
    <div className="max-w-xl mx-auto pb-10 space-y-8 animate-fadein">
      <div className="flex items-center justify-between">
        <button onClick={() => navigate(-1)} className="p-3 rounded-2xl bg-navy-900 border border-navy-700 text-slate-400">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-xl font-bold text-slate-100">Abrir Chamado</h1>
        <div className="w-10" />
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Step 1: Asset */}
        <div className="space-y-4">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Ativo Selecionado</label>
          <div className="relative">
             <select
               disabled={!!initialId}
               value={form.assetId}
               onChange={e => setForm({ ...form, assetId: e.target.value })}
               className="w-full bg-navy-900 border border-navy-700 rounded-3xl px-6 py-5 text-lg font-black text-blue-400 outline-none appearance-none disabled:opacity-80 shadow-2xl"
             >
               <option value="">Escolha seu veículo...</option>
               <optgroup label="Veículos">
                 {vehicles.map(v => <option key={v.id} value={`VEHICLE:${v.id}`}>{v.plate} — {v.model}</option>)}
               </optgroup>
               <optgroup label="Embarcações">
                 {boats.map(b => <option key={b.id} value={`BOAT:${b.id}`}>{b.name} — {b.model}</option>)}
               </optgroup>
             </select>
             {!initialId && <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500">
                <Car className="w-6 h-6" />
             </div>}
          </div>
        </div>

        {/* Step 2: Urgency Grid */}
        <div className="space-y-4">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Nível de Urgência</label>
          <div className="grid grid-cols-2 gap-3">
             {urgencyOptions.map(opt => (
               <button
                 key={opt.id}
                 type="button"
                 onClick={() => setForm({ ...form, urgency: opt.id })}
                 className={`p-4 rounded-3xl border transition-all text-left ${
                   form.urgency === opt.id 
                     ? `bg-blue-500 border-blue-400 shadow-xl shadow-blue-500/20` 
                     : `bg-navy-900 border-navy-700`
                 }`}
               >
                 <div className={`text-xs font-bold uppercase tracking-wider ${form.urgency === opt.id ? 'text-white' : opt.color}`}>
                   {opt.label}
                 </div>
               </button>
             ))}
          </div>
        </div>

        {/* Step 3: Description */}
        <div className="space-y-4">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">O que está acontecendo?</label>
          <textarea
            value={form.problemDescription}
            onChange={e => setForm({ ...form, problemDescription: e.target.value })}
            placeholder="Relate barulhos, luzes no painel ou serviços desejados..."
            className="w-full min-h-[160px] bg-navy-900 border border-navy-700 rounded-3xl p-6 text-slate-100 placeholder:text-slate-600 outline-none focus:border-blue-500/50 shadow-inner"
          />
        </div>

        {/* Step 4: Photos (Camera Focus) */}
        <div className="space-y-4">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Evidências (Fotos)</label>
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 custom-scrollbar">
             <label className="shrink-0 w-24 h-24 rounded-3xl bg-blue-500/10 border-2 border-dashed border-blue-500/30 flex flex-col items-center justify-center text-blue-400 active:scale-95 transition-all cursor-pointer">
                <Camera className="w-8 h-8" />
                <span className="text-[10px] font-bold mt-1 uppercase tracking-tighter">Câmera</span>
                <input type="file" multiple accept="image/*" onChange={handlePhotoChange} className="hidden" />
             </label>
             {previews.map((src, i) => (
               <div key={i} className="shrink-0 w-24 h-24 rounded-3xl border border-navy-700 relative overflow-hidden shadow-lg">
                  <img src={src} className="w-full h-full object-cover" />
                  <button onClick={() => removePhoto(i)} className="absolute top-1 right-1 p-1 bg-black/60 rounded-full text-white">
                     <X className="w-3 h-3" />
                  </button>
               </div>
             ))}
          </div>
        </div>

        {/* Submit */}
        <div className="pt-6">
          {error && <div className="mb-4 text-center text-red-400 text-xs font-bold uppercase">{error}</div>}
          <button
            type="submit"
            disabled={sending}
            className="w-full bg-blue-500 py-6 rounded-3xl text-lg font-black text-white shadow-2xl shadow-blue-500/30 flex items-center justify-center gap-3 active:scale-[0.98] transition-all disabled:opacity-50"
          >
            {sending ? <Clock className="w-6 h-6 animate-spin" /> : <Send className="w-6 h-6" />}
            {sending ? 'ENVIANDO...' : 'ENVIAR CHAMADO'}
          </button>
        </div>
      </form>
    </div>
  )
}
