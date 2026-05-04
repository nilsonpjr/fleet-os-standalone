import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState } from 'react'
import { Truck, Lock, Mail, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { useAuthStore, AuthUser } from '@core/auth/store'
import api from '@core/api/client'

const schema = z.object({
  email: z.string().email('E-mail inválido'),
  password: z.string().min(6, 'Mínimo 6 caracteres'),
})
type FormData = z.infer<typeof schema>

export default function LoginPage() {
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)
  const [showPw, setShowPw] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setServerError(null)
    try {
      // Step 1: get token (form-encoded)
      const formData = new URLSearchParams()
      formData.append('username', data.email)
      formData.append('password', data.password)

      formData.append('grant_type', 'password')

      const tokenRes = await api.postForm<{ access_token: string; token_type: string }>(
        '/api/auth/login',
        formData
      )

      // Temporarily store token so /me can use it
      localStorage.setItem('access_token', tokenRes.access_token)

      // Step 2: fetch user profile
      const me = await api.get<{
        id: number; name: string; email: string; role: string;
        tenant_id: number; client_id?: number;
      }>('/api/auth/me')

      const user: AuthUser = {
        id: me.id,
        name: me.name,
        email: me.email,
        role: me.role as AuthUser['role'],
        tenantId: me.tenant_id,
        clientId: me.client_id,
      }

      login(tokenRes.access_token, user)

      // Route by role
      if (user.role === 'CLIENT') navigate('/client/dashboard')
      else if (user.role === 'PARTNER') navigate('/workshop/dashboard')
      else navigate('/admin/dashboard')
    } catch (err: unknown) {
      localStorage.removeItem('access_token')
      setServerError(typeof err === 'string' ? err : 'Credenciais inválidas')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-navy-950 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-amber-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-blue-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-amber-500/10 border border-amber-500/20 rounded-2xl mb-4">
            <Truck className="w-8 h-8 text-amber-400" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100">FleetOS</h1>
          <p className="text-slate-400 text-sm mt-1">Sistema de Gestão de Frotas</p>
        </div>

        {/* Card */}
        <div className="glass rounded-2xl p-8 shadow-2xl">
          <h2 className="text-lg font-semibold text-slate-200 mb-6">Acesso ao Sistema</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email */}
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                E-mail
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  {...register('email')}
                  type="email"
                  autoComplete="email"
                  placeholder="seu@email.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-navy-900 border border-navy-700 rounded-xl text-slate-100 text-sm placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500/60 transition-all"
                />
              </div>
              {errors.email && (
                <p className="text-red-400 text-xs mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                Senha
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  {...register('password')}
                  type={showPw ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="w-full pl-10 pr-10 py-2.5 bg-navy-900 border border-navy-700 rounded-xl text-slate-100 text-sm placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500/60 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-red-400 text-xs mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {errors.password.message}
                </p>
              )}
            </div>

            {/* Server error */}
            {serverError && (
              <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {serverError}
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 mt-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-navy-950 font-bold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm shadow-lg shadow-amber-500/20"
            >
              {isSubmitting ? 'Entrando...' : 'Entrar'}
            </button>
          </form>

          {/* Portal hints */}
          <div className="mt-6 pt-5 border-t border-navy-700 grid grid-cols-3 gap-2">
            {[
              { label: 'Gestora', className: 'text-amber-400', desc: 'Admin/Manager' },
              { label: 'Cliente', className: 'text-blue-400', desc: 'Solicitante' },
              { label: 'Oficina', className: 'text-emerald-400', desc: 'Parceiro' },
            ].map((p) => (
              <div key={p.label} className="text-center">
                <div className={`text-xs font-bold ${p.className}`}>{p.label}</div>
                <div className="text-[10px] text-slate-600">{p.desc}</div>
              </div>
            ))}
          </div>
        </div>

        <p className="text-center text-slate-600 text-xs mt-6">
          FleetOS © {new Date().getFullYear()} · Gestão Inteligente de Frotas
        </p>
      </div>
    </div>
  )
}
