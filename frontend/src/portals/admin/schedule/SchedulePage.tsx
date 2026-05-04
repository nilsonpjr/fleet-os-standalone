import { useState, useMemo } from 'react'
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Clock, MapPin, Wrench, Package, Search, Filter } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useApi } from '@shared/hooks/useApi'
import api from '@core/api/client'
import { StatusBadge, TableSkeleton } from '@shared/components/ui'

export default function SchedulePage() {
  const navigate = useNavigate()
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [search, setSearch] = useState('')
  
  const { data: requests = [], loading } = useApi<any[]>(() => 
    api.get('/api/fleet/requests', { status: 'IN_PROGRESS,ASSIGNED,CLIENT_APPROVED' })
  )

  const weekDays = useMemo(() => {
    const days = []
    const start = new Date(selectedDate)
    start.setDate(selectedDate.getDate() - selectedDate.getDay())
    
    for (let i = 0; i < 7; i++) {
      const d = new Date(start)
      d.setDate(start.getDate() + i)
      days.push(d)
    }
    return days
  }, [selectedDate])

  const filteredRequests = useMemo(() => {
    return requests.filter(r => {
      const needle = search.toLowerCase()
      return r.client?.name.toLowerCase().includes(needle) || 
             r.vehicle?.plate.toLowerCase().includes(needle) ||
             r.problem_description.toLowerCase().includes(needle)
    })
  }, [requests, search])

  const handlePrevWeek = () => {
    const d = new Date(selectedDate)
    d.setDate(d.getDate() - 7)
    setSelectedDate(d)
  }

  const handleNextWeek = () => {
    const d = new Date(selectedDate)
    d.setDate(d.getDate() + 7)
    setSelectedDate(d)
  }

  return (
    <div className="space-y-6 animate-fadein pb-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Agenda de Serviços</h1>
          <p className="text-slate-400 text-sm mt-0.5">Planejamento semanal de manutenções e reparos.</p>
        </div>
        <div className="flex gap-2">
           <div className="bg-navy-800 border border-navy-700 rounded-xl p-1 flex">
              <button onClick={handlePrevWeek} className="p-1.5 hover:bg-navy-700 rounded-lg text-slate-400 transition-all">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <div className="px-3 py-1.5 text-xs font-bold text-slate-200">
                {weekDays[0].toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })} — {weekDays[6].toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}
              </div>
              <button onClick={handleNextWeek} className="p-1.5 hover:bg-navy-700 rounded-lg text-slate-400 transition-all">
                <ChevronRight className="w-4 h-4" />
              </button>
           </div>
        </div>
      </div>

      {/* Week Timeline */}
      <div className="grid grid-cols-7 gap-2">
        {weekDays.map((date, i) => {
          const isToday = date.toDateString() === new Date().toDateString()
          const isSelected = date.toDateString() === selectedDate.toDateString()
          
          return (
            <button
              key={i}
              onClick={() => setSelectedDate(date)}
              className={`flex flex-col items-center py-3 rounded-2xl border transition-all ${
                isSelected 
                  ? 'bg-amber-500 border-amber-400 text-navy-950 shadow-lg shadow-amber-500/20' 
                  : isToday 
                    ? 'bg-navy-800 border-amber-500/50 text-amber-500' 
                    : 'bg-navy-900 border-navy-700 text-slate-500 hover:border-navy-600'
              }`}
            >
              <span className="text-[10px] font-bold uppercase mb-1">{date.toLocaleDateString('pt-BR', { weekday: 'short' })}</span>
              <span className="text-lg font-black">{date.getDate()}</span>
            </button>
          )
        })}
      </div>

      {/* Search & Filters */}
      <div className="bg-navy-800 border border-navy-700 rounded-2xl p-4 flex gap-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input 
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Pesquisar placa, cliente ou serviço..."
            className="w-full bg-navy-900 border border-navy-700 rounded-xl pl-9 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500/50 transition-all"
          />
        </div>
        <button className="px-4 py-2 bg-navy-900 border border-navy-700 rounded-xl text-slate-400 hover:text-slate-200 transition-all flex items-center gap-2 text-sm">
          <Filter className="w-4 h-4" /> Filtros
        </button>
      </div>

      {/* Services List */}
      <div className="space-y-4">
        {loading ? (
          <TableSkeleton rows={4} />
        ) : filteredRequests.length === 0 ? (
          <div className="py-20 text-center bg-navy-900/30 rounded-3xl border-2 border-dashed border-navy-800">
            <CalendarIcon className="w-12 h-12 text-slate-700 mx-auto mb-4" />
            <p className="text-slate-500 font-medium">Nenhum serviço agendado para este período.</p>
          </div>
        ) : (
          filteredRequests.map((req) => (
            <div 
              key={req.id} 
              onClick={() => navigate(`/admin/requests/${req.id}`)}
              className="bg-navy-800 border border-navy-700 rounded-3xl p-5 flex flex-col md:flex-row gap-6 hover:border-navy-600 cursor-pointer transition-all group"
            >
              {/* Left: Time & Asset */}
              <div className="flex gap-4 md:w-64 shrink-0">
                <div className="w-12 h-12 rounded-2xl bg-navy-900 border border-navy-700 flex flex-col items-center justify-center text-amber-500">
                  <Clock className="w-5 h-5" />
                  <span className="text-[9px] font-bold mt-0.5">09:30</span>
                </div>
                <div>
                  <h3 className="font-bold text-slate-100 uppercase tracking-tighter">{req.vehicle?.plate || req.boat?.name}</h3>
                  <p className="text-[10px] text-slate-500 font-bold uppercase">{req.client?.name}</p>
                </div>
              </div>

              {/* Middle: Description */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <StatusBadge status={req.status} />
                  <span className="text-[10px] font-bold text-slate-600 uppercase flex items-center gap-1">
                    <Wrench className="w-3 h-3" /> Mecânica
                  </span>
                </div>
                <p className="text-sm text-slate-300 line-clamp-2 italic leading-relaxed">
                  "{req.problem_description}"
                </p>
              </div>

              {/* Right: Workshop & Price */}
              <div className="flex items-center justify-between md:justify-end gap-6 md:w-64">
                <div className="text-right">
                   <p className="text-[10px] font-bold text-slate-500 uppercase flex items-center justify-end gap-1">
                      <MapPin className="w-3 h-3" /> Oficina Atribuída
                   </p>
                   <p className="text-xs text-slate-200 font-bold">{req.quotes?.[0]?.workshop?.name || 'Aguardando'}</p>
                </div>
                <div className="p-3 rounded-2xl bg-navy-900 border border-navy-700 group-hover:bg-navy-700 transition-all">
                  <ChevronRight className="w-5 h-5 text-slate-500" />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

