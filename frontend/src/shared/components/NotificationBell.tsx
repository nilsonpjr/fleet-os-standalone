import { useState, useEffect, useRef } from 'react'
import { Bell, Check, Trash2, ExternalLink, Info, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import api from '@core/api/client'

interface Notification {
  id: number
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  is_read: boolean
  link?: string
  created_at: string
}

export default function NotificationBell() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const fetchNotifications = async () => {
    try {
      const res = await api.get<any>('/notifications')
      const list = Array.isArray(res)
        ? res
        : Array.isArray(res?.items)
          ? res.items
          : Array.isArray(res?.data)
            ? res.data
            : []
      setNotifications(list)
    } catch (err) {
      console.error('Erro ao buscar notificações:', err)
      setNotifications([])
    }
  }

  useEffect(() => {
    fetchNotifications()
    // Polling every 30 seconds
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const unreadCount = notifications.filter(n => !n.is_read).length

  const markAsRead = async (id: number) => {
    try {
      await api.patch(`/notifications/${id}/read`)
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
    } catch (err) {
      console.error('Erro ao marcar como lida:', err)
    }
  }

  const markAllAsRead = async () => {
    try {
      await api.post('/notifications/read-all')
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
    } catch (err) {
      console.error('Erro ao marcar todas como lidas:', err)
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'success': return <CheckCircle className="w-4 h-4 text-emerald-500" />
      case 'warning': return <AlertTriangle className="w-4 h-4 text-amber-500" />
      case 'error': return <XCircle className="w-4 h-4 text-rose-500" />
      default: return <Info className="w-4 h-4 text-blue-500" />
    }
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-xl bg-navy-800/50 border border-navy-700 hover:border-blue-500/50 transition-all group"
      >
        <Bell className="w-5 h-5 text-slate-400 group-hover:text-blue-400 transition-colors" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white ring-2 ring-navy-900 animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-3 w-80 md:w-96 rounded-2xl bg-navy-900/95 backdrop-blur-xl border border-navy-700 shadow-2xl z-50 overflow-hidden transform origin-top-right transition-all">
          <div className="p-4 border-b border-navy-700 flex items-center justify-between bg-navy-800/30">
            <h3 className="font-semibold text-slate-200 flex items-center gap-2">
              Notificações
              <span className="text-xs font-normal text-slate-500">({notifications.length})</span>
            </h3>
            {unreadCount > 0 && (
              <button 
                onClick={markAllAsRead}
                className="text-xs text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
              >
                <Check className="w-3 h-3" />
                Ler todas
              </button>
            )}
          </div>

          <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
            {notifications.length === 0 ? (
              <div className="p-8 text-center">
                <div className="w-12 h-12 bg-navy-800 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Bell className="w-6 h-6 text-slate-600" />
                </div>
                <p className="text-sm text-slate-500">Nenhuma notificação por enquanto.</p>
              </div>
            ) : (
              <div className="divide-y divide-navy-800">
                {notifications.map((n) => (
                  <div 
                    key={n.id} 
                    className={`p-4 hover:bg-navy-800/40 transition-colors relative group ${!n.is_read ? 'bg-blue-500/5' : ''}`}
                  >
                    <div className="flex gap-3">
                      <div className="mt-1">
                        {getTypeIcon(n.type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className={`text-sm font-medium ${!n.is_read ? 'text-slate-100' : 'text-slate-400'}`}>
                            {n.title}
                          </h4>
                          <span className="text-[10px] text-slate-500 whitespace-nowrap">
                            {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 line-clamp-2 mb-2">
                          {n.message}
                        </p>
                        <div className="flex items-center gap-3">
                          {n.link && (
                            <Link 
                              to={n.link} 
                              onClick={() => { markAsRead(n.id); setIsOpen(false) }}
                              className="text-[10px] font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
                            >
                              Ver detalhes
                              <ExternalLink className="w-2 h-2" />
                            </Link>
                          )}
                          {!n.is_read && (
                            <button 
                              onClick={() => markAsRead(n.id)}
                              className="text-[10px] font-semibold text-slate-500 hover:text-slate-300"
                            >
                              Marcar como lida
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                    {!n.is_read && (
                      <div className="absolute top-4 right-2 w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="p-3 border-t border-navy-700 bg-navy-800/30 text-center">
            <button className="text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors">
              Ver histórico completo
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
