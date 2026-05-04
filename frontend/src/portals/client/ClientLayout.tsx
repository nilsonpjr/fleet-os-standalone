import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { ClipboardList, Car, Bell, LogOut, User, Smartphone, Plus } from 'lucide-react'
import { useAuthStore } from '@core/auth/store'
import NotificationBell from '@shared/components/NotificationBell'

const clientNav = [
  { to: '/client/dashboard', icon: Smartphone, label: 'Home' },
  { to: '/client/my-fleet',  icon: Car,        label: 'Frota' },
]

const clientNavSecondary = [
  { to: '/client/requests',  icon: ClipboardList, label: 'Chamados' },
  { to: '/client/profile',   icon: User,          label: 'Perfil' },
]

export default function ClientLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  return (
    <div className="flex flex-col h-screen bg-navy-950 portal-client text-slate-100 overflow-hidden">
      {/* Premium Top Header */}
      <header className="bg-navy-900/50 backdrop-blur-xl border-b border-navy-700/50 px-5 py-3 flex items-center justify-between shrink-0 z-40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-blue-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <User className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="text-[10px] text-blue-400 font-bold uppercase tracking-wider">Bem-vindo,</p>
            <h2 className="text-sm font-bold truncate max-w-[150px]">{user?.name?.split(' ')[0]}</h2>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
            <NotificationBell />
           <button
             onClick={() => { logout(); navigate('/login') }}
             className="p-2.5 rounded-2xl bg-navy-800/50 border border-navy-700 text-slate-400 hover:text-red-400 transition-all"
           >
             <LogOut className="w-5 h-5" />
           </button>
        </div>
      </header>

      {/* Main Scrollable Content */}
      <main className="flex-1 overflow-y-auto pb-28 pt-4 px-4 custom-scrollbar bg-gradient-to-b from-navy-950 to-navy-900">
        <Outlet />
      </main>

      {/* Premium Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 h-24 bg-navy-900/80 backdrop-blur-2xl border-t border-navy-700/50 flex items-center justify-around px-2 pb-6 z-50">
        {clientNav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex flex-col items-center gap-1.5 px-3 transition-all relative
              ${isActive ? 'text-blue-400' : 'text-slate-500'}`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={`w-6 h-6 transition-transform ${isActive ? 'scale-110' : ''}`} />
                <span className="text-[10px] font-bold">{item.label}</span>
                {isActive && <div className="absolute -top-3 w-6 h-1 bg-blue-500 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.5)]" />}
              </>
            )}
          </NavLink>
        ))}

        {/* Central Quick Action Button */}
        <div className="relative -mt-12 group">
           <button 
             onClick={() => navigate('/client/requests/new')}
             className="w-16 h-16 rounded-full bg-blue-500 flex items-center justify-center shadow-2xl shadow-blue-500/40 border-4 border-navy-950 group-active:scale-95 transition-all"
           >
             <Plus className="w-8 h-8 text-white" />
           </button>
           <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 text-[10px] font-bold text-blue-400 whitespace-nowrap">Solicitar</span>
        </div>

        {clientNavSecondary.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex flex-col items-center gap-1.5 px-3 transition-all relative
              ${isActive ? 'text-blue-400' : 'text-slate-500'}`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={`w-6 h-6 transition-transform ${isActive ? 'scale-110' : ''}`} />
                <span className="text-[10px] font-bold">{item.label}</span>
                {isActive && <div className="absolute -top-3 w-6 h-1 bg-blue-500 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.5)]" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Safe Area Notch Padding (for mobile browsers) */}
      <div className="h-safe-bottom bg-navy-900/80" />
    </div>
  )
}
