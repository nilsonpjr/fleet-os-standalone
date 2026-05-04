import { useState } from 'react'
import { X, Camera, Upload, Check, Loader2 } from 'lucide-react'

interface PhotoUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onUpload: (files: File[]) => Promise<void>
  title: string
  subtitle?: string
}

export default function PhotoUploadModal({ isOpen, onClose, onUpload, title, subtitle }: PhotoUploadModalProps) {
  const [files, setFiles] = useState<File[]>([])
  const [previews, setPreviews] = useState<string[]>([])
  const [uploading, setUploading] = useState(false)

  if (!isOpen) return null

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files)
      setFiles(prev => [...prev, ...newFiles])
      const newPreviews = newFiles.map(f => URL.createObjectURL(f))
      setPreviews(prev => [...prev, ...newPreviews])
    }
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
    setPreviews(prev => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) return
    setUploading(true)
    try {
      await onUpload(files)
      setFiles([])
      setPreviews([])
      onClose()
    } catch (err) {
      console.error('Upload failed:', err)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/80 backdrop-blur-sm animate-fadein">
      <div className="bg-navy-900 border-t sm:border border-navy-700 w-full max-w-lg rounded-t-3xl sm:rounded-3xl overflow-hidden shadow-2xl animate-slideUp">
        <div className="px-6 py-5 border-b border-navy-700 flex items-center justify-between bg-navy-800/50">
          <div>
            <h3 className="text-lg font-bold text-slate-100">{title}</h3>
            {subtitle && <p className="text-xs text-slate-500 font-medium uppercase tracking-widest mt-1">{subtitle}</p>}
          </div>
          <button onClick={onClose} className="p-2 rounded-xl bg-navy-900 border border-navy-700 text-slate-400">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Dropzone/Capture */}
          <div className="grid grid-cols-2 gap-4">
             <label className="flex flex-col items-center justify-center gap-2 p-8 rounded-2xl bg-blue-500/10 border-2 border-dashed border-blue-500/30 text-blue-400 hover:bg-blue-500/20 transition-all cursor-pointer">
                <Camera className="w-8 h-8" />
                <span className="text-[10px] font-bold uppercase">Câmera</span>
                <input type="file" accept="image/*" capture="environment" onChange={handleFileChange} className="hidden" />
             </label>
             <label className="flex flex-col items-center justify-center gap-2 p-8 rounded-2xl bg-navy-800 border border-navy-700 text-slate-400 hover:bg-navy-700 transition-all cursor-pointer">
                <Upload className="w-8 h-8" />
                <span className="text-[10px] font-bold uppercase">Galeria</span>
                <input type="file" multiple accept="image/*" onChange={handleFileChange} className="hidden" />
             </label>
          </div>

          {/* Previews */}
          {previews.length > 0 && (
            <div className="grid grid-cols-3 gap-3 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
              {previews.map((src, i) => (
                <div key={i} className="relative aspect-square rounded-xl border border-navy-700 overflow-hidden shadow-lg group">
                  <img src={src} className="w-full h-full object-cover" />
                  <button 
                    onClick={() => removeFile(i)}
                    className="absolute top-1 right-1 p-1 bg-black/60 rounded-full text-white opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          <button
            onClick={handleUpload}
            disabled={files.length === 0 || uploading}
            className="w-full py-4 rounded-2xl bg-blue-500 text-white font-black uppercase tracking-widest shadow-xl shadow-blue-500/20 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-3"
          >
            {uploading ? <Loader2 className="w-6 h-6 animate-spin" /> : <Check className="w-6 h-6" />}
            {uploading ? 'ENVIANDO...' : `ENVIAR ${files.length} FOTO${files.length !== 1 ? 'S' : ''}`}
          </button>
        </div>
      </div>
    </div>
  )
}
