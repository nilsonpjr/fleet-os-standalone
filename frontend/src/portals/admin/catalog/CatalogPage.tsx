import { useState, useMemo } from 'react'
import { Search, Plus, Package, Wrench, Boxes, MoreVertical, Pencil, Trash2, Tag, ShieldCheck } from 'lucide-react'
import { EmptyState, TableSkeleton, StatusBadge } from '@shared/components/ui'

export default function CatalogPage() {
  const [activeTab, setActiveTab] = useState('PARTS')
  const [search, setSearch] = useState('')
  const [loading] = useState(false) // TODO: Connect API

  const tabs = [
    { id: 'PARTS', label: 'Peças', icon: Package, color: 'blue' },
    { id: 'SERVICES', label: 'Serviços', icon: Wrench, color: 'amber' },
    { id: 'KITS', label: 'Kits de Manutenção', icon: Boxes, color: 'emerald' },
  ]

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
          <div className="flex gap-2">
            <button className="px-3 py-1.5 rounded-lg border border-navy-700 text-[10px] font-bold text-slate-500 uppercase hover:text-slate-300 transition-colors">Filtrar Categoria</button>
            <button className="px-3 py-1.5 rounded-lg border border-navy-700 text-[10px] font-bold text-slate-500 uppercase hover:text-slate-300 transition-colors">Exportar</button>
          </div>
        </div>

        {loading ? (
          <TableSkeleton rows={8} />
        ) : (
          <div className="overflow-x-auto">
             <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-navy-700 text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-navy-900/20">
                    <th className="px-6 py-4">Item / Código</th>
                    <th className="px-6 py-4">Categoria</th>
                    <th className="px-6 py-4 text-right">Preço Base</th>
                    <th className="px-6 py-4 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-navy-700">
                   {/* Placeholder Data */}
                   {[1,2,3,4,5].map(i => (
                     <tr key={i} className="hover:bg-navy-700/30 transition-all group">
                        <td className="px-6 py-4">
                           <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl bg-navy-900 border border-navy-700 flex items-center justify-center text-slate-500 group-hover:text-emerald-400 transition-colors">
                                 {activeTab === 'PARTS' ? <Package className="w-5 h-5" /> : <Wrench className="w-5 h-5" />}
                              </div>
                              <div>
                                 <p className="text-sm font-bold text-slate-200">Item Exemplo #{i}</p>
                                 <p className="text-[10px] text-slate-500 font-mono">SKU-00{i}-DEMO</p>
                              </div>
                           </div>
                        </td>
                        <td className="px-6 py-4">
                           <span className="text-[9px] font-bold px-2 py-0.5 rounded border border-navy-600 bg-navy-900 text-slate-400 uppercase tracking-tighter">
                              {activeTab === 'PARTS' ? 'Peças de Motor' : 'Mão de Obra'}
                           </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                           <p className="text-xs font-bold text-emerald-400">R$ {(i * 150).toFixed(2)}</p>
                           <p className="text-[9px] text-slate-600 uppercase">Sugestão Venda</p>
                        </td>
                        <td className="px-6 py-4 text-right">
                           <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button className="p-2 rounded-lg bg-navy-900 border border-navy-700 text-slate-400 hover:text-emerald-500 transition-all">
                                 <Pencil className="w-4 h-4" />
                              </button>
                              <button className="p-2 rounded-lg bg-navy-900 border border-navy-700 text-slate-400 hover:text-red-400 transition-all">
                                 <Trash2 className="w-4 h-4" />
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
