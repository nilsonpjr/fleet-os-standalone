import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Ship, Anchor, Wrench, FileText, Settings, ShieldCheck, History, TrendingUp } from 'lucide-react'
import api from '@core/api/client'
import { useApi } from '@shared/hooks/useApi'
import AssetHistoryTab from '@shared/components/AssetHistoryTab'
import AssetCostStats from '@shared/components/AssetCostStats'
import AssetHealthCard from '@shared/components/AssetHealthCard'
import { CreateBoatModal } from './components/CreateBoatModal'

export default function BoatDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('GERAL')
  const [showEditModal, setShowEditModal] = useState(false)

  const { data: boat, loading, error, mutate } = useApi<any>(() => 
    api.get(`/api/boats/${id}`)
  )

  const { data: regulatory } = useApi<any>(() => 
    api.get(`/api/boats/${id}/regulatory`)
  )

  if (loading) return <div className="p-10 text-center text-slate-500">Carregando detalhes da embarcação...</div>
  if (error || !boat) return <div className="p-10 text-center text-red-400">{error || 'Embarcação não encontrada'}</div>

  const tabs = [
    { id: 'GERAL', label: 'Dados Gerais', icon: <Ship className="w-4 h-4" /> },
    { id: 'REGULATORY', label: 'Documentação', icon: <Anchor className="w-4 h-4" /> },
    { id: 'MOTORES', label: 'Motores', icon: <Wrench className="w-4 h-4" /> },
    { id: 'HISTORY', label: 'Histórico', icon: <History className="w-4 h-4" /> },
    { id: 'STATS', label: 'Estatísticas', icon: <TrendingUp className="w-4 h-4" /> },
  ]

  return (
    <div className="space-y-6 animate-fadein">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/admin/boats')}
            className="p-2 rounded-xl bg-navy-800 border border-navy-700 text-slate-400 hover:text-slate-200 transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-100">{boat.name}</h1>
            <p className="text-slate-400 text-sm">{boat.brand} {boat.model} • {boat.client?.name}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => setShowEditModal(true)}
            className="px-4 py-2 rounded-xl border border-navy-700 text-slate-300 font-bold hover:bg-navy-800 transition-all text-sm flex items-center gap-2"
          >
            <Settings className="w-4 h-4" /> Editar
          </button>
          <button className="px-4 py-2 rounded-xl bg-sky-500 text-white font-bold hover:bg-sky-400 transition-all text-sm flex items-center gap-2">
            <ShieldCheck className="w-4 h-4" /> Ativo
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-navy-700 gap-1 overflow-x-auto no-scrollbar">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-6 py-3 text-sm font-bold flex items-center gap-2 transition-all whitespace-nowrap border-b-2 ${
              activeTab === t.id ? 'border-sky-500 text-sky-400 bg-sky-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {activeTab === 'GERAL' && (
            <>
              <AssetHealthCard boatId={boat.id} />
              <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 space-y-8 shadow-xl shadow-black/10">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                <div>
                  <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Marca / Estaleiro</div>
                  <div className="text-slate-100 font-medium">{boat.brand}</div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Modelo</div>
                  <div className="text-slate-100 font-medium">{boat.model}</div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Ano</div>
                  <div className="text-slate-100 font-medium">{boat.year}</div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Comprimento</div>
                  <div className="text-slate-100 font-medium">{boat.length_ft || '—'} pés</div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Tipo</div>
                  <div className="text-slate-100 font-medium">{boat.type || 'Lancha'}</div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Cor do Casco</div>
                  <div className="text-slate-100 font-medium">{boat.hull_color || '—'}</div>
                </div>
              </div>
              
              <div className="pt-6 border-t border-navy-700">
                <div className="text-[10px] font-bold text-slate-500 uppercase mb-2">Observações</div>
                <p className="text-sm text-slate-400 italic">"{boat.notes || 'Nenhuma observação cadastrada.'}"</p>
              </div>
            </div>
          </>
          )}

          {activeTab === 'REGULATORY' && (
            <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 space-y-8 shadow-xl shadow-black/10">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-6">
                  <h3 className="text-xs font-bold text-sky-400 uppercase tracking-[0.2em] flex items-center gap-2">
                    <FileText className="w-4 h-4" /> Marinha do Brasil
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-xl bg-navy-900 border border-navy-700">
                      <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">TMC / Registro</div>
                      <div className="text-slate-100 font-plate text-sm">{regulatory?.registration_number || '—'}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-navy-900 border border-navy-700">
                      <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Validade TMC</div>
                      <div className="text-slate-100 font-bold text-sm">{regulatory?.registration_expiry || '—'}</div>
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-navy-900 border border-navy-700">
                    <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Autoridade de Registro</div>
                    <div className="text-slate-100 text-sm font-medium">{regulatory?.registration_authority || '—'}</div>
                  </div>
                </div>

                <div className="space-y-6">
                  <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-[0.2em] flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4" /> Seguro Náutico
                  </h3>
                  <div className="p-3 rounded-xl bg-navy-900 border border-navy-700">
                    <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Seguradora / Apólice</div>
                    <div className="text-slate-100 text-sm font-medium">{regulatory?.insurance_company || '—'} · {regulatory?.insurance_policy || '—'}</div>
                  </div>
                  <div className="p-3 rounded-xl bg-navy-900 border border-navy-700">
                    <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Vencimento do Seguro</div>
                    <div className="text-slate-100 text-sm font-bold">{regulatory?.insurance_expiry || '—'}</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'MOTORES' && (
            <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 shadow-xl shadow-black/10">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-sm font-bold text-slate-200 uppercase tracking-widest">Motores Instalados</h3>
                <button className="text-xs text-sky-400 font-bold hover:underline">+ Adicionar Motor</button>
              </div>
              <div className="space-y-4">
                {(boat.engines || []).map((engine: any, i: number) => (
                  <div key={i} className="p-4 rounded-2xl bg-navy-900 border border-navy-700 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-navy-800 border border-navy-700 flex items-center justify-center text-slate-500">
                        <Settings className="w-6 h-6" />
                      </div>
                      <div>
                        <div className="text-slate-100 font-bold">{engine.brand} {engine.hp}HP</div>
                        <div className="text-xs text-slate-500">S/N: {engine.serial_number}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-slate-100">{engine.hours}h</div>
                      <div className="text-[10px] text-slate-500 font-bold uppercase">Horímetro</div>
                    </div>
                  </div>
                ))}
                {(!boat.engines || boat.engines.length === 0) && (
                  <div className="py-8 text-center border-2 border-dashed border-navy-700 rounded-2xl">
                    <Wrench className="w-10 h-10 text-slate-700 mx-auto mb-2" />
                    <p className="text-slate-500 text-sm">Nenhum motor cadastrado para esta embarcação.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'HISTORY' && (
            <AssetHistoryTab boatId={boat.id} />
          )}

          {activeTab === 'STATS' && (
            <AssetCostStats boatId={boat.id} />
          )}
        </div>

        <div className="space-y-6">
          {/* Quick Actions / Summary */}
          <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 space-y-6">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Informações de Gestão</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Última Revisão</span>
                <span className="text-xs text-slate-200 font-bold">12/02/2026</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Próxima Manutenção</span>
                <span className="text-xs text-amber-500 font-bold">Aguardando Horímetro</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Status Financeiro</span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                  Adimplente
                </span>
              </div>
            </div>

            <button 
              onClick={() => navigate(`/admin/requests/new?boatId=${boat.id}`)}
              className="w-full py-3 rounded-xl bg-navy-900 border border-navy-700 text-slate-300 font-bold hover:bg-navy-800 transition-all text-sm"
            >
              Abrir OS para este Barco
            </button>
          </div>
        </div>
      </div>

      {showEditModal && (
        <CreateBoatModal 
          onClose={() => setShowEditModal(false)}
          onSuccess={() => { mutate(); }}
          initialData={boat}
        />
      )}
    </div>
  )
}
