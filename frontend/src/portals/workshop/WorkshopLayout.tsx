import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LayoutDashboard, ClipboardList, CheckSquare, LogOut, Wrench, Bell, Settings2 } from 'lucide-react'
import { useAuthStore } from '@core/auth/store'
import NotificationBell from '@shared/components/NotificationBell'

const workshopNav = [
  { to: '/workshop/dashboard', icon: <LayoutDashboard className="w-5 h-5" />, label: 'Painel' },
  { to: '/workshop/requests',  icon: <ClipboardList className="w-5 h-5" />,   label: 'Solicitações' },
  { to: '/workshop/execution', icon: <CheckSquare className="w-5 h-5" />,     label: 'Em Execução' },
  { to: '/workshop/settings',  icon: <Settings2 className="w-5 h-5" />,       label: 'Configurações' },
]

export default function WorkshopLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  return (
    <div className="flex h-screen bg-navy-950 portal-workshop overflow-hidden">
      {/* Compact sidebar */}
      <aside className="w-60 bg-navy-900 border-r border-navy-700 flex flex-col">
        <div className="p-4 border-b border-navy-700">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Wrench className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="font-bold text-slate-100 text-sm">FleetOS</div>
              <div className="text-[10px] text-emerald-400">Portal da Oficina</div>
            </div>
          </div>
          <div className="mt-3 px-2 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
            <div className="text-xs font-bold text-slate-300 truncate">{user?.name}</div>
          </div>
        </div>

        <nav className="flex-1 p-2 space-y-0.5">
          {workshopNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all
                ${isActive
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'text-slate-400 hover:bg-navy-800 hover:text-slate-200'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span className={isActive ? 'text-emerald-400' : 'text-slate-500'}>{item.icon}</span>
                  {item.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-2 border-t border-navy-700">
          <button
            onClick={() => { logout(); navigate('/login') }}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-all"
          >
            <LogOut className="w-4 h-4" /> Sair
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-[65px] bg-navy-900/80 backdrop-blur border-b border-navy-700 flex items-center px-6 gap-4 shrink-0">
          <div className="flex-1" />
          <NotificationBell />
        </header>
        <main className="flex-1 overflow-y-auto p-6 animate-fadein">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
