import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore, UserRole } from '@core/auth/store'

interface Props {
  allowedRoles?: UserRole[]
}

export default function PrivateRoute({ allowedRoles }: Props) {
  const { isAuthenticated, user } = useAuthStore()

  if (!isAuthenticated || !user) return <Navigate to="/login" replace />

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect to correct portal
    if (user.role === 'CLIENT') return <Navigate to="/client/dashboard" replace />
    if (user.role === 'PARTNER') return <Navigate to="/workshop/dashboard" replace />
    return <Navigate to="/admin/dashboard" replace />
  }

  return <Outlet />
}
