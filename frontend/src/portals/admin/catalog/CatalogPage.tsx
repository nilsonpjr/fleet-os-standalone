import { useState, useMemo } from 'react'
import { Search, Plus, Package, Wrench, Boxes, Pencil, Tag, ShieldCheck, RefreshCw } from 'lucide-react'
import { EmptyState, TableSkeleton } from '@shared/components/ui'
import { useApi } from '@shared/hooks/useApi'
import api from '@core/api/client'

export default function CatalogPage() {
  const [activeTab, setActiveTab] = useState('PARTS')
  const [search, setSearch] = useState('')

  const { data: parts = [], loading: loadingParts, refetch: refetchParts } = useApi<any[]>(() => api.get('/api/inventory/parts'))
  const { data: services = [], loading: loadingServices } = useApi<any[]>(() => api.get('/api/config/service-definitions'))
  const { data: kits = [], loading: loadingKits } = useApi<any[]>(() => api.get('/api/inventory/kits'))

  const loading = activeTab === 'PARTS' ? loadingParts : activeTab === 'KITS' ? loadingKits : loadingServices

  const tabs = [
    { id: 'PARTS', label: 'Peças', icon: Package, color: 'blue' },
    { id: 'SERVICES', label: 'Serviços', icon: Wrench, color: 'amber' },
    { id: 'KITS', label: 'Kits de Manutenção', icon: Boxes, color: 'emerald' },
  ]

  const filtered = useMemo(() => {
    const needle = search.toLowerCase()
    if (activeTab === 'PARTS') {
      return parts.filter(p =>
        p.name?.toLowerCase().includes(needle) ||
        p.sku?.toLowerCase().includes(needle) ||
        p.category?.toLowerCase().includes(needle)
      )
    }
    if (activeTab === 'SERVICES') {
      return services.filter(s =>
        s.name?.toLowerCase().includes(needle) ||
        s.category?.toLowerCase().includes(needle) ||
        s.code?.toLowerCase().includes(needle)
      )
    }
    if (activeTab === 'KITS') {
      return kits.filter(k =>
        k.name?.toLowerCase().includes(needle)
      )
    }
    return []
  }, [parts, services, kits, activeTab, search])

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0)

  return (
    <div className="space-y-6 animate-fadein">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Boxes className="w-6 h-6 text-emerald-400" />
            Catálogo Mestre
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">Padronização de itens para orçamentos e faturamento.</p>
        </div>
        <button className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-500 text-navy-950 font-bold hover:bg-emerald-400 transition-all text-sm shadow-lg shadow-emerald-500/20">
          <Plus className="w-4 h-4" />
          {activeTab === 'KITS' ? 'Novo Kit' : activeTab === 'SERVICES' ? 'Novo Serviço' : 'Nova Peça'}
        </button>
      </div>

      <div className="flex gap-2 border-b border-navy-700 pb-px">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-6 py-4 text-xs font-bold flex items-center gap-2 transition-all border-b-2 ${
              activeTab === tab.id 
                ? 'border-emerald-500 text-emerald-400' 
                : 'border-transparent text-slate-500 hover:text-slate-300'
            }`}
          >
            <tab.icon className={`w-4 h-4 ${activeTab === tab.id ? 'text-emerald-400' : 'text-slate-500'}`} />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="bg-navy-800 border border-navy-700 rounded-3xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-navy-700 bg-navy-900/50 flex flex-wrap items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input 
              value={search} onChange={e => setSearch(e.target.value)}
              placeholder={`Buscar em ${tabs.find(t => t.id === activeTab)?.label.toLowerCase()}...`}
              className="w-full pl-10 pr-4 py-2.5 bg-navy-900 border border-navy-700 rounded-xl text-sm text-slate-200 outline-none focus:border-emerald-500/50 transition-all"
            />
          </div>
          <button
            onClick={refetchParts}
            className="p-2.5 rounded-xl border border-navy-700 text-slate-500 hover:bg-navy-700 transition-all"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {loading ? (
          <TableSkeleton rows={8} />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<Package className="w-10 h-10" />}
            title="Nenhum item encontrado"
            description={activeTab === 'SERVICES' ? 'Nenhum serviço cadastrado. Adicione através do botão acima.' : 'Cadastre peças ou kits para usar em orçamentos.'}
          />
        ) : (
          <div className="overflow-x-auto">
             <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-navy-700 text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-navy-900/20">
                    <th className="px-6 py-4">Item / Código</th>
                    <th className="px-6 py-4">Categoria</th>
                    {activeTab === 'PARTS' && <th className="px-6 py-4 text-right">Estoque</th>}
                    <th className="px-6 py-4 text-right">Preço Base</th>
                    <th className="px-6 py-4 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-navy-700">
                   {filtered.map(item => (
                     <tr key={item.id} className="hover:bg-navy-700/30 transition-all group">
                        <td className="px-6 py-4">
                           <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl bg-navy-900 border border-navy-700 flex items-center justify-center text-slate-500 group-hover:text-emerald-400 transition-colors">
                                 {activeTab === 'PARTS' ? <Package className="w-5 h-5" /> : <Boxes className="w-5 h-5" />}
                              </div>
                              <div>
                                 <p className="text-sm font-bold text-slate-200">{item.name}</p>
                                 <p className="text-[10px] text-slate-500 font-mono">{item.sku || item.code || `ID-${item.id}`}</p>
                              </div>
                           </div>
                        </td>
                        <td className="px-6 py-4">
                           <span className="text-[9px] font-bold px-2 py-0.5 rounded border border-navy-600 bg-navy-900 text-slate-400 uppercase tracking-tighter">
                              {item.category || item.group || item.vehicle_type || 'Geral'}
                           </span>
                        </td>
                        {activeTab === 'PARTS' && (
                          <td className="px-6 py-4 text-right">
                            <p className={`text-xs font-bold ${(item.stock_quantity || 0) <= (item.min_stock || 0) ? 'text-red-400' : 'text-slate-300'}`}>
                              {item.stock_quantity || 0}
                            </p>
                            <p className="text-[9px] text-slate-600 uppercase">unidades</p>
                          </td>
                        )}
                        <td className="px-6 py-4 text-right">
                           <p className="text-xs font-bold text-emerald-400">{formatCurrency(item.price || item.default_price || item.sale_price || item.cost_price || 0)}</p>
                           <p className="text-[9px] text-slate-600 uppercase">Preço</p>
                        </td>
                        <td className="px-6 py-4 text-right">
                           <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button className="p-2 rounded-lg bg-navy-900 border border-navy-700 text-slate-400 hover:text-emerald-500 transition-all">
                                 <Pencil className="w-4 h-4" />
                              </button>
                           </div>
                        </td>
                     </tr>
                   ))}
                </tbody>
             </table>
          </div>
        )}
      </div>

      {/* Kit Preview Card (Only on KITS tab) */}
      {activeTab === 'KITS' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
           <div className="p-6 rounded-3xl bg-emerald-500/5 border border-emerald-500/10 flex gap-4">
              <div className="p-3 rounded-2xl bg-emerald-500/10 text-emerald-500 h-fit">
                 <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                 <h4 className="text-sm font-bold text-emerald-200">Kits Homologados</h4>
                 <p className="text-xs text-emerald-500/70 mt-1">Kits agilizam o orçamento e garantem que nenhuma peça crítica seja esquecida na manutenção preventiva.</p>
              </div>
           </div>
        </div>
      )}
    </div>
  )
}
