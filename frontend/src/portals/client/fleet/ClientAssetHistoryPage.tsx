import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, Car, Ship } from 'lucide-react'
import AssetHistoryTab from '@shared/components/AssetHistoryTab'

export default function ClientAssetHistoryPage() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const type = searchParams.get('type') || 'VEHICLE'

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadein">
      <div className="flex items-center gap-4">
        <button 
          onClick={() => navigate(-1)}
          className="p-2 rounded-xl bg-navy-800 border border-navy-700 text-slate-400 hover:text-slate-200 transition-all"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            {type === 'VEHICLE' ? <Car className="w-6 h-6 text-amber-500" /> : <Ship className="w-6 h-6 text-sky-400" />}
            Histórico de Manutenção
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">Veja tudo o que já foi feito neste ativo.</p>
        </div>
      </div>

      <div className="bg-navy-800 border border-navy-700 rounded-3xl p-6 shadow-xl shadow-black/20">
        <AssetHistoryTab 
          vehicleId={type === 'VEHICLE' ? parseInt(id!) : undefined} 
          boatId={type === 'BOAT' ? parseInt(id!) : undefined} 
        />
      </div>
    </div>
  )
}
