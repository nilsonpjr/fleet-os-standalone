import { useState, useEffect, useRef } from 'react'
import { Send, User as UserIcon, Clock } from 'lucide-react'
import api from '@core/api/client'
import { useAuthStore } from '@core/auth/store'

interface Message {
  id: number
  user_id: number
  user_name: string
  message: string
  created_at: string
}

interface ChatWidgetProps {
  requestId: number
}

export default function ChatWidget({ requestId }: ChatWidgetProps) {
  const { user } = useAuthStore()
  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const chatContainerRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }

  const fetchMessages = async () => {
    try {
      const res = await api.get<any>(`/api/fleet/requests/${requestId}/messages`)
      setMessages(Array.isArray(res) ? res : (res?.data || []))
    } catch (err) {
      console.error('Erro ao buscar mensagens:', err)
    }
  }

  useEffect(() => {
    fetchMessages()
    const interval = setInterval(fetchMessages, 5000) // Polling every 5s
    return () => clearInterval(interval)
  }, [requestId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || loading) return

    setLoading(true)
    try {
      const res = await api.post<any>(`/api/fleet/requests/${requestId}/messages`, {
        message: newMessage
      })
      const newMsg = res?.data ?? res
      setMessages(prev => [...prev, newMsg])
      setNewMessage('')
    } catch (err) {
      alert('Erro ao enviar mensagem')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-navy-900 border border-navy-700 rounded-3xl overflow-hidden flex flex-col h-[500px] shadow-2xl">
      <div className="p-4 border-b border-navy-700 bg-navy-800/30 flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-200">Chat do Chamado</h3>
        <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-widest flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Online
        </span>
      </div>

      <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-navy-950/20">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-40">
             <div className="w-12 h-12 bg-navy-800 rounded-full flex items-center justify-center mb-2">
                <Send className="w-6 h-6 text-slate-600" />
             </div>
             <p className="text-xs text-slate-500">Nenhuma mensagem ainda.<br/>Inicie a conversa sobre este serviço.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`flex flex-col ${msg.user_id === user?.id ? 'items-end' : 'items-start'}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase">{msg.user_name}</span>
                <span className="text-[9px] text-slate-600">
                  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <div className={`
                max-w-[85%] px-4 py-2.5 rounded-2xl text-sm shadow-sm
                ${msg.user_id === user?.id 
                  ? 'bg-blue-600 text-white rounded-tr-none' 
                  : 'bg-navy-800 text-slate-200 border border-navy-700 rounded-tl-none'}
              `}>
                {msg.message}
              </div>
            </div>
          ))
        )}
      </div>

      <form onSubmit={handleSendMessage} className="p-4 border-t border-navy-700 bg-navy-800/30">
        <div className="flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Digite sua mensagem..."
            className="flex-1 bg-navy-950 border border-navy-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-all"
          />
          <button
            type="submit"
            disabled={loading || !newMessage.trim()}
            className="w-11 h-11 rounded-xl bg-blue-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/20 active:scale-95 disabled:opacity-50 transition-all"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  )
}
