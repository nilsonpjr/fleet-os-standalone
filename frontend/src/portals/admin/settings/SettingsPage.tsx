import { useEffect, useMemo, useState } from 'react'
import { Building2, Save, Settings2, ShieldCheck, Wallet, Wrench } from 'lucide-react'
import api from '@core/api/client'

type CompanyConfig = {
  company_name: string
  trade_name: string
  cnpj: string
  ie: string
  im: string
  phone: string
  whatsapp: string
  instagram: string
  street: string
  number: string
  neighborhood: string
  city: string
  state: string
  zip_code: string
  fiscal_environment: string
  city_code: string
  mercury_username: string
  mercury_password: string
  n8n_webhook_url: string
  pix_enabled: boolean
  pix_key: string
  pix_key_type: string
  pix_bank_name: string
  labor_rate_low: string
  labor_rate_medium: string
  labor_rate_high: string
}

const EMPTY_FORM: CompanyConfig = {
  company_name: '',
  trade_name: '',
  cnpj: '',
  ie: '',
  im: '',
  phone: '',
  whatsapp: '',
  instagram: '',
  street: '',
  number: '',
  neighborhood: '',
  city: '',
  state: '',
  zip_code: '',
  fiscal_environment: 'homologation',
  city_code: '4118204',
  mercury_username: '',
  mercury_password: '',
  n8n_webhook_url: '',
  pix_enabled: false,
  pix_key: '',
  pix_key_type: '',
  pix_bank_name: '',
  labor_rate_low: '0',
  labor_rate_medium: '0',
  labor_rate_high: '0',
}

function toNumberOrZero(value: string) {
  const normalized = value.replace(',', '.').trim()
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : 0
}

function inputClassName() {
  return 'w-full px-4 py-2.5 rounded-xl bg-navy-900 border border-navy-700 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-amber-500 transition-all'
}

export default function SettingsPage() {
  const [form, setForm] = useState<CompanyConfig>(EMPTY_FORM)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const config = await api.get<Partial<CompanyConfig> | null>('/api/config/company')
        if (!config) return
        setForm((prev) => ({
          ...prev,
          ...config,
          fiscal_environment: config.fiscal_environment ?? prev.fiscal_environment,
          city_code: config.city_code ?? prev.city_code,
          labor_rate_low: String(config.labor_rate_low ?? prev.labor_rate_low),
          labor_rate_medium: String(config.labor_rate_medium ?? prev.labor_rate_medium),
          labor_rate_high: String(config.labor_rate_high ?? prev.labor_rate_high),
          pix_enabled: Boolean(config.pix_enabled),
        }))
      } catch (e) {
        setError(typeof e === 'string' ? e : 'Não foi possível carregar as configurações.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const canSave = useMemo(() => !saving && !loading, [saving, loading])

  const onChange = (key: keyof CompanyConfig, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [key]: value }))
    setMessage(null)
    setError(null)
  }

  const onSave = async () => {
    setSaving(true)
    setMessage(null)
    setError(null)
    try {
      const payload = {
        ...form,
        labor_rate_low: toNumberOrZero(form.labor_rate_low),
        labor_rate_medium: toNumberOrZero(form.labor_rate_medium),
        labor_rate_high: toNumberOrZero(form.labor_rate_high),
      }
      await api.put('/api/config/company', payload)
      setMessage('Configurações salvas com sucesso.')
    } catch (e) {
      setError(typeof e === 'string' ? e : 'Falha ao salvar configurações.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6 animate-fadein pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Configurações</h1>
          <p className="text-slate-400 text-sm">Dados da empresa, integrações e parâmetros operacionais.</p>
        </div>
        <button
          onClick={onSave}
          disabled={!canSave}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500 text-navy-950 text-sm font-bold hover:bg-amber-400 transition-all disabled:opacity-60"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Salvando...' : 'Salvar Alterações'}
        </button>
      </div>

      {error && <div className="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-sm">{error}</div>}
      {message && <div className="px-4 py-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 text-sm">{message}</div>}

      <section className="bg-navy-800 border border-navy-700 rounded-2xl p-5 space-y-4">
        <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Building2 className="w-4 h-4 text-amber-400" />
          Identificação da Empresa
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input value={form.company_name} onChange={(e) => onChange('company_name', e.target.value)} placeholder="Razão social" className={inputClassName()} />
          <input value={form.trade_name} onChange={(e) => onChange('trade_name', e.target.value)} placeholder="Nome fantasia" className={inputClassName()} />
          <input value={form.cnpj} onChange={(e) => onChange('cnpj', e.target.value)} placeholder="CNPJ" className={inputClassName()} />
          <input value={form.ie} onChange={(e) => onChange('ie', e.target.value)} placeholder="Inscrição estadual" className={inputClassName()} />
          <input value={form.im} onChange={(e) => onChange('im', e.target.value)} placeholder="Inscrição municipal" className={inputClassName()} />
          <input value={form.city_code} onChange={(e) => onChange('city_code', e.target.value)} placeholder="Código IBGE da cidade" className={inputClassName()} />
        </div>
      </section>

      <section className="bg-navy-800 border border-navy-700 rounded-2xl p-5 space-y-4">
        <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Settings2 className="w-4 h-4 text-blue-400" />
          Contato e Endereço
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input value={form.phone} onChange={(e) => onChange('phone', e.target.value)} placeholder="Telefone" className={inputClassName()} />
          <input value={form.whatsapp} onChange={(e) => onChange('whatsapp', e.target.value)} placeholder="WhatsApp" className={inputClassName()} />
          <input value={form.instagram} onChange={(e) => onChange('instagram', e.target.value)} placeholder="Instagram" className={inputClassName()} />
          <input value={form.street} onChange={(e) => onChange('street', e.target.value)} placeholder="Rua / Logradouro" className={inputClassName()} />
          <input value={form.number} onChange={(e) => onChange('number', e.target.value)} placeholder="Número" className={inputClassName()} />
          <input value={form.neighborhood} onChange={(e) => onChange('neighborhood', e.target.value)} placeholder="Bairro" className={inputClassName()} />
          <input value={form.city} onChange={(e) => onChange('city', e.target.value)} placeholder="Cidade" className={inputClassName()} />
          <input value={form.state} onChange={(e) => onChange('state', e.target.value)} placeholder="UF" className={inputClassName()} />
          <input value={form.zip_code} onChange={(e) => onChange('zip_code', e.target.value)} placeholder="CEP" className={inputClassName()} />
        </div>
      </section>

      <section className="bg-navy-800 border border-navy-700 rounded-2xl p-5 space-y-4">
        <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Fiscal e Integrações
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <select value={form.fiscal_environment} onChange={(e) => onChange('fiscal_environment', e.target.value)} className={inputClassName()}>
            <option value="homologation">Homologação</option>
            <option value="production">Produção</option>
          </select>
          <input value={form.mercury_username} onChange={(e) => onChange('mercury_username', e.target.value)} placeholder="Mercury usuário" className={inputClassName()} />
          <input type="password" value={form.mercury_password} onChange={(e) => onChange('mercury_password', e.target.value)} placeholder="Mercury senha" className={inputClassName()} />
          <input value={form.n8n_webhook_url} onChange={(e) => onChange('n8n_webhook_url', e.target.value)} placeholder="Webhook n8n" className="md:col-span-3 w-full px-4 py-2.5 rounded-xl bg-navy-900 border border-navy-700 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-amber-500 transition-all" />
        </div>
      </section>

      <section className="bg-navy-800 border border-navy-700 rounded-2xl p-5 space-y-4">
        <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Wallet className="w-4 h-4 text-sky-400" />
          PIX
        </h2>
        <label className="inline-flex items-center gap-2 text-sm text-slate-300">
          <input type="checkbox" checked={form.pix_enabled} onChange={(e) => onChange('pix_enabled', e.target.checked)} className="rounded border-navy-700 bg-navy-900" />
          Habilitar PIX
        </label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input value={form.pix_key} onChange={(e) => onChange('pix_key', e.target.value)} placeholder="Chave PIX" className={inputClassName()} />
          <input value={form.pix_key_type} onChange={(e) => onChange('pix_key_type', e.target.value)} placeholder="Tipo (CPF/CNPJ/EMAIL/ALEATORIA)" className={inputClassName()} />
          <input value={form.pix_bank_name} onChange={(e) => onChange('pix_bank_name', e.target.value)} placeholder="Banco" className={inputClassName()} />
        </div>
      </section>

      <section className="bg-navy-800 border border-navy-700 rounded-2xl p-5 space-y-4">
        <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Wrench className="w-4 h-4 text-amber-400" />
          Tabela de Mão de Obra (R$/h)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input value={form.labor_rate_low} onChange={(e) => onChange('labor_rate_low', e.target.value)} placeholder="Baixa complexidade" className={inputClassName()} />
          <input value={form.labor_rate_medium} onChange={(e) => onChange('labor_rate_medium', e.target.value)} placeholder="Média complexidade" className={inputClassName()} />
          <input value={form.labor_rate_high} onChange={(e) => onChange('labor_rate_high', e.target.value)} placeholder="Alta complexidade" className={inputClassName()} />
        </div>
      </section>
    </div>
  )
}
