import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type UserRole = 'ADMIN' | 'MANAGER' | 'CLIENT' | 'PARTNER' | 'TECHNICIAN'
export type Portal = 'admin' | 'client' | 'workshop'

export interface AuthUser {
  id: number
  name: string
  email: string
  role: UserRole
  tenantId: number
  tenantName?: string
  clientId?: number
  partnerId?: number
}

interface AuthState {
  user: AuthUser | null
  token: string | null
  portal: Portal | null
  isAuthenticated: boolean
  login: (token: string, user: AuthUser) => void
  logout: () => void
}

function resolvePortal(role: UserRole): Portal {
  if (role === 'CLIENT') return 'client'
  if (role === 'PARTNER') return 'workshop'
  return 'admin'
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      portal: null,
      isAuthenticated: false,

      login: (token, user) => {
        localStorage.setItem('access_token', token)
        set({
          token,
          user,
          portal: resolvePortal(user.role),
          isAuthenticated: true,
        })
      },

      logout: () => {
        localStorage.removeItem('access_token')
        set({ token: null, user: null, portal: null, isAuthenticated: false })
      },
    }),
    {
      name: 'fleetos-auth',
      partialize: (s) => ({ token: s.token, user: s.user, portal: s.portal, isAuthenticated: s.isAuthenticated }),
    }
  )
)
