import { useState, useEffect } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Car, Ship, Users, Wrench, ClipboardList,
  Package, Calendar, BarChart2, Settings, LogOut, ChevronLeft,
  ChevronRight, Bell, Menu, X, Truck
} from 'lucide-react'
import { useAuthStore } from '@core/auth/store'
import NotificationBell from '@shared/components/NotificationBell'
import api from '@core/api/client'

interface NavItem {
  to: string
  icon: React.ReactNode
  label: string
  badge?: number
}

export default function AdminLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [alertCount, setAlertCount] = useState(3)

  const adminNav: NavItem[] = [
    { to: '/admin/dashboard',    icon: <LayoutDashboard className="w-5 h-5" />, label: 'Dashboard' },
    { to: '/admin/vehicles',     icon: <Car className="w-5 h-5" />,            label: 'Veículos' },
    { to: '/admin/boats',        icon: <Ship className="w-5 h-5" />,           label: 'Embarcações' },
    { to: '/admin/clients',      icon: <Users className="w-5 h-5" />,          label: 'Clientes' },
    { to: '/admin/workshops',    icon: <Wrench className="w-5 h-5" />,         label: 'Oficinas' },
    { to: '/admin/requests',     icon: <ClipboardList className="w-5 h-5" />,  label: 'Solicitações' },
    { to: '/admin/alerts',       icon: <Bell className="w-5 h-5" />,           label: 'Alertas', badge: alertCount },
    { to: '/admin/catalog',      icon: <Package className="w-5 h-5" />,        label: 'Catálogo' },
    { to: '/admin/schedule',     icon: <Calendar className="w-5 h-5" />,       label: 'Agenda' },
    { to: '/admin/reports',      icon: <BarChart2 className="w-5 h-5" />,      label: 'Relatórios' },
    { to: '/admin/settings',     icon: <Settings className="w-5 h-5" />,       label: 'Configurações' },
  ]

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const [expiry, maint] = await Promise.all([
          api.get<any[]>('/api/fleet/alerts').catch(() => []),
          api.get<any[]>('/api/fleet/maintenance/alerts').catch(() => []),
        ])
        setAlertCount(expiry.length + maint.length)
      } catch (err) {
        console.error('Failed to fetch sidebar alerts', err)
      }
    }
    fetchAlerts()
    const interval = setInterval(fetchAlerts, 60000) // Refresh every minute
    return () => clearInterval(interval)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const Sidebar = () => (
    <aside
      className={`
        flex flex-col h-full bg-navy-900 border-r border-navy-700 transition-all duration-300
        ${collapsed ? 'w-[72px]' : 'w-64'}
      `}
    >
      {/* Logo */}
      <div className={`flex items-center gap-3 p-4 border-b border-navy-700 min-h-[65px] ${collapsed ? 'justify-center' : ''}`}>
        <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0">
          <Truck className="w-5 h-5 text-amber-400" />
        </div>
        {!collapsed && (
          <div>
            <div className="font-bold text-slate-100 text-sm leading-tight">FleetOS</div>
            <div className="text-[10px] text-amber-500 font-medium">Gestora</div>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 overflow-y-auto space-y-0.5 px-2">
        {adminNav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group
              ${isActive
                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                : 'text-slate-400 hover:bg-navy-800 hover:text-slate-200'
              }
              ${collapsed ? 'justify-center' : ''}`
            }
            title={collapsed ? item.label : undefined}
          >
            {({ isActive }) => (
              <>
                <span className={isActive ? 'text-amber-400' : 'text-slate-500 group-hover:text-slate-300'}>
                  {item.icon}
                </span>
                {!collapsed && <span className="truncate">{item.label}</span>}
                {!collapsed && item.badge && item.badge > 0 && (
                  <span className="ml-auto bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                    {item.badge}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User + collapse */}
      <div className="p-2 border-t border-navy-700 space-y-1">
        {!collapsed && (
          <div className="px-3 py-2 rounded-xl bg-navy-800/50">
            <div className="text-xs font-bold text-slate-300 truncate">{user?.name}</div>
            <div className="text-[10px] text-amber-500">{user?.role}</div>
          </div>
        )}
        <button
          onClick={handleLogout}
          className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-all ${collapsed ? 'justify-center' : ''}`}
        >
          <LogOut className="w-4 h-4" />
          {!collapsed && 'Sair'}
        </button>
        <button
          onClick={() => setCollapsed((v) => !v)}
          className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-xs text-slate-500 hover:bg-navy-800 hover:text-slate-300 transition-all ${collapsed ? 'justify-center' : ''}`}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <><ChevronLeft className="w-4 h-4" /><span>Recolher</span></>}
        </button>
      </div>
    </aside>
  )

  return (
    <div className="flex h-screen bg-navy-950 overflow-hidden portal-admin print:h-auto print:overflow-visible">
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex shrink-0 print:hidden">
        <Sidebar />
      </div>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden print:hidden">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="absolute left-0 top-0 h-full w-64">
            <Sidebar />
          </div>
        </div>
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="h-[65px] bg-navy-900/80 backdrop-blur border-b border-navy-700 flex items-center px-4 gap-4 shrink-0 print:hidden">
          <button
            className="lg:hidden text-slate-400 hover:text-slate-200"
            onClick={() => setMobileOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex-1" />

          <NotificationBell />
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 animate-fadein print:p-0 print:overflow-visible">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
