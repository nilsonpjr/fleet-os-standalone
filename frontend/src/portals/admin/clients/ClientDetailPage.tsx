import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  ArrowLeft, User, Building2, Car, Ship, FileText, 
  TrendingUp, Calendar, MapPin, Phone, Mail, ShieldCheck,
  AlertTriangle, History, Pencil
} from 'lucide-react'
import { useApi } from '@shared/hooks/useApi'
import api from '@core/api/client'
import { TableSkeleton } from '@shared/components/ui'
import { KpiCard } from '@shared/components/KpiCard'
import ClientFormModal from './ClientFormModal'

export default function ClientDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('OVERVIEW')
  const [showEditModal, setShowEditModal] = useState(false)
  const [saving, setSaving] = useState(false)

  const { data: client, loading: loadingClient, refetch: refetchClient } = useApi<any>(() => api.get(`/api/clients/${id}`))
  const { data: detail, loading: loadingDetail, refetch: refetchDetail } = useApi<any>(() => api.get(`/api/fleet/clients/${id}/detail`))
  const { data: fleet = [], loading: loadingFleet } = useApi<any[]>(() => api.get(`/api/fleet/assets?client_id=${id}`))
  const { data: orders = [] } = useApi<any[]>(() => api.get(`/api/orders?client_id=${id}`))

  if (loadingClient || loadingDetail) return <TableSkeleton rows={10} />
  if (!client) return <div>Cliente não encontrado</div>

  const vehicles = fleet.filter(a => a.type === 'VEHICLE')
  const boats = fleet.filter(a => a.type === 'BOAT')
  const totalSpent = orders.reduce((acc, o) => acc + (o.total_value || 0), 0)

  const tabs = [
    { id: 'OVERVIEW', label: 'Visão Geral', icon: TrendingUp },
    { id: 'FLEET', label: 'Frota', icon: Car },
    { id: 'ORDERS', label: 'Histórico de OS', icon: History },
    { id: 'CONTRACT', label: 'Contrato & Faturamento', icon: FileText },
  ]

  const handleEditSubmit = async (formData: any) => {
    try {
      setSaving(true)
      // First update the core client data
      await api.put(`/api/clients/${id}`, {
        name: formData.name,
        document: formData.document,
        type: formData.type,
        phone: formData.phone,
        email: formData.email,
        address: formData.address,
      })

      // Then update the detail/contract data
      await api.put(`/api/fleet/clients/${id}/detail`, {
        company_name: formData.company_name,
        cnpj: formData.cnpj,
        ie: formData.ie,
        im: formData.im,
        crt: formData.crt,
        billing_address: formData.billing_address,
        billing_city: formData.billing_city,
        billing_state: formData.billing_state,
        billing_zip: formData.billing_zip,
        contract_type: formData.contract_type,
        contract_value: formData.contract_value ? Number(formData.contract_value) : undefined,
        contract_start: formData.contract_start || undefined,
        contract_end: formData.contract_end || undefined,
      })

      await Promise.all([refetchClient(), refetchDetail()])
      setShowEditModal(false)
    } catch (error) {
      console.error('Failed to update client', error)
      alert('Erro ao atualizar cliente')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6 animate-fadein pb-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/admin/clients')} className="p-2 rounded-xl bg-navy-800 border border-navy-700 text-slate-400 hover:text-slate-100 transition-all">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-100">{client.name}</h1>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${client.type === 'PJ' ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' : 'bg-slate-700/30 border-slate-600 text-slate-400'}`}>
                {client.type || 'PF'}
              </span>
            </div>
            <p className="text-slate-400 text-sm mt-0.5">{client.document} • {client.email || 'Sem e-mail'}</p>
          </div>
        </div>
        <button 
          onClick={() => setShowEditModal(true)}
          className="px-4 py-2 rounded-xl border border-navy-700 text-slate-300 text-xs font-bold flex items-center gap-2 hover:bg-navy-800 transition-all"
        >
          <Pencil className="w-4 h-4" /> Editar Cadastro
        </button>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Veículos" value={vehicles.length} subtitle="em operação" icon={<Car className="w-5 h-5" />} accentColor="amber" />
        <KpiCard title="Embarcações" value={boats.length} subtitle="na frota" icon={<Ship className="w-5 h-5" />} accentColor="sky" />
        <KpiCard title="Total Gasto" value={new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(totalSpent)} subtitle="em toda vigência" icon={<TrendingUp className="w-5 h-5" />} accentColor="emerald" />
        <KpiCard title="OS Concluídas" value={orders.filter(o => o.status === 'DONE').length} subtitle={`${orders.length} total`} icon={<ShieldCheck className="w-5 h-5" />} accentColor="blue" />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-navy-700 pb-px">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-6 py-3 text-xs font-bold flex items-center gap-2 transition-all border-b-2 ${
              activeTab === tab.id 
                ? 'border-amber-500 text-amber-500' 
                : 'border-transparent text-slate-500 hover:text-slate-300'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="animate-fadein">
        {activeTab === 'OVERVIEW' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 space-y-6">
                 <h3 className="text-sm font-bold text-slate-200 border-b border-navy-700 pb-4">Informações de Contato</h3>
                 <div className="grid grid-cols-2 gap-8">
                    <div className="space-y-4">
                       <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-navy-900 border border-navy-700 flex items-center justify-center text-slate-500">
                             <Phone className="w-4 h-4" />
                          </div>
                          <div>
                             <p className="text-[10px] font-bold text-slate-500 uppercase">Telefone</p>
                             <p className="text-sm text-slate-200">{client.phone || '—'}</p>
                          </div>
                       </div>
                       <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-navy-900 border border-navy-700 flex items-center justify-center text-slate-500">
                             <Mail className="w-4 h-4" />
                          </div>
                          <div>
                             <p className="text-[10px] font-bold text-slate-500 uppercase">E-mail</p>
                             <p className="text-sm text-slate-200">{client.email || '—'}</p>
                          </div>
                       </div>
                    </div>
                    <div className="space-y-4">
                       <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-navy-900 border border-navy-700 flex items-center justify-center text-slate-500">
                             <MapPin className="w-4 h-4" />
                          </div>
                          <div>
                             <p className="text-[10px] font-bold text-slate-500 uppercase">Endereço Principal</p>
                             <p className="text-sm text-slate-200">{client.address || '—'}</p>
                          </div>
                       </div>
                    </div>
                 </div>
              </div>
            </div>
            
            <div className="space-y-6">
               <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6">
                  <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-sky-400" /> Resumo do Contrato
                  </h3>
                  {detail ? (
                    <div className="space-y-4">
                       <div className="flex justify-between items-center py-2 border-b border-navy-700">
                          <span className="text-xs text-slate-500">Tipo</span>
                          <span className="text-xs font-bold text-slate-200">{detail.contract_type}</span>
                       </div>
                       <div className="flex justify-between items-center py-2 border-b border-navy-700">
                          <span className="text-xs text-slate-500">Valor Mensal</span>
                          <span className="text-xs font-bold text-emerald-400">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(detail.contract_value || 0)}</span>
                       </div>
                       <div className="flex justify-between items-center py-2">
                          <span className="text-xs text-slate-500">Vigência</span>
                          <span className="text-xs font-bold text-slate-200">{detail.contract_start}</span>
                       </div>
                    </div>
                  ) : (
                    <div className="py-4 text-center">
                       <AlertTriangle className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                       <p className="text-xs text-slate-500">Nenhum contrato ativo configurado.</p>
                    </div>
                  )}
               </div>
            </div>
          </div>
        )}

        {activeTab === 'FLEET' && (
          <div className="bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden">
             <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-navy-700 text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-navy-900/20">
                    <th className="px-6 py-4">Ativo</th>
                    <th className="px-6 py-4">Identificação</th>
                    <th className="px-6 py-4">Uso Atual</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-navy-700">
                  {fleet.map(a => (
                    <tr key={a.id} className="hover:bg-navy-700/30 transition-all cursor-pointer" onClick={() => navigate(a.type === 'BOAT' ? `/admin/boats/${a.id}` : `/admin/vehicles/${a.id}`)}>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                           {a.type === 'BOAT' ? <Ship className="w-5 h-5 text-sky-400" /> : <Car className="w-5 h-5 text-amber-500" />}
                           <div className="text-sm font-bold text-slate-200">{a.brand} {a.model}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-xs text-slate-300 font-medium">{a.plate || a.name}</p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-xs text-slate-400">{a.mileage_current || a.hours_current || 0} {a.type === 'VEHICLE' ? 'km' : 'horas'}</p>
                      </td>
                    </tr>
                  ))}
                </tbody>
             </table>
          </div>
        )}

        {activeTab === 'ORDERS' && (
          <div className="bg-navy-800 border border-navy-700 rounded-2xl overflow-hidden">
             {orders.length === 0 ? (
               <div className="p-20 text-center">
                 <History className="w-12 h-12 text-slate-700 mx-auto mb-4" />
                 <p className="text-slate-500 font-medium">Nenhum histórico de manutenção encontrado.</p>
               </div>
             ) : (
               <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-navy-700 text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-navy-900/20">
                      <th className="px-6 py-4">ID / Data</th>
                      <th className="px-6 py-4">Ativo</th>
                      <th className="px-6 py-4">Status</th>
                      <th className="px-6 py-4 text-right">Valor</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-navy-700">
                    {orders.map(o => (
                      <tr key={o.id} className="hover:bg-navy-700/30 transition-all cursor-pointer">
                        <td className="px-6 py-4">
                          <p className="text-xs font-bold text-slate-200">#{o.id}</p>
                          <p className="text-[10px] text-slate-500">{new Date(o.created_at).toLocaleDateString()}</p>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-xs text-slate-300 font-medium">{o.asset_name || 'Ativo Geral'}</p>
                        </td>
                        <td className="px-6 py-4">
                           <span className={`text-[9px] font-bold px-2 py-0.5 rounded-lg border ${
                             o.status === 'DONE' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                             o.status === 'CANCELLED' ? 'bg-red-500/10 border-red-500/20 text-red-400' :
                             'bg-amber-500/10 border-amber-500/20 text-amber-400'
                           }`}>
                             {o.status}
                           </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <p className="text-xs font-bold text-slate-200">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(o.total_value || 0)}</p>
                        </td>
                      </tr>
                    ))}
                  </tbody>
               </table>
             )}
          </div>
        )}

        {activeTab === 'CONTRACT' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 space-y-6">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" /> Detalhes Fiscais (PJ)
              </h3>
              {detail ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-[10px] font-bold text-slate-500 uppercase">CNPJ</p>
                      <p className="text-sm text-slate-200 font-mono">{detail.cnpj || '—'}</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-500 uppercase">Inc. Estadual</p>
                      <p className="text-sm text-slate-200 font-mono">{detail.ie || '—'}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-slate-500 uppercase">Endereço de Faturamento</p>
                    <p className="text-sm text-slate-200">{detail.billing_address || '—'}</p>
                    <p className="text-xs text-slate-500">{detail.billing_city} - {detail.billing_state}</p>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">Dados fiscais adicionais não cadastrados.</p>
              )}
            </div>

            <div className="bg-navy-800 border border-navy-700 rounded-2xl p-6 space-y-6">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <FileText className="w-4 h-4 text-sky-400" /> Condições do Contrato
              </h3>
              {detail ? (
                <div className="space-y-4">
                   <div className="p-4 rounded-xl bg-navy-900 border border-navy-700">
                      <div className="flex justify-between items-center mb-1">
                         <span className="text-xs font-bold text-slate-100 uppercase tracking-widest">{detail.contract_type}</span>
                         <span className="text-sm font-bold text-emerald-400">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(detail.contract_value || 0)}/mês</span>
                      </div>
                      <p className="text-[10px] text-slate-500">Renovação automática em {detail.contract_end || 'fluxo contínuo'}</p>
                   </div>
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">Vínculo de contrato não configurado.</p>
              )}
            </div>
          </div>
        )}
      </div>

      <ClientFormModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        onSave={handleEditSubmit}
        initialData={{ ...client, ...detail }}
        loading={saving}
      />
    </div>
  )
}
