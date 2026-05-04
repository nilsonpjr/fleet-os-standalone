/* ── FleetOS Global Types ─────────────────────────────────── */

export type UserRole = 'ADMIN' | 'MANAGER' | 'CLIENT' | 'PARTNER' | 'TECHNICIAN'

// ── Request Status Machine ─────────────────────────────────
export type RequestStatus =
  | 'OPEN'
  | 'ASSIGNED'
  | 'QUOTED'           // quotes submitted, waiting admin review
  | 'ADMIN_APPROVED'   // admin approved, waiting client
  | 'CLIENT_APPROVED'  // both approved → go to execution
  | 'REVISION_REQUESTED'
  | 'IN_PROGRESS'
  | 'AWAITING_CLOSURE' // workshop done, waiting admin+client sign-off
  | 'ADMIN_CLOSED'     // admin approved closure
  | 'CLIENT_CLOSED'    // client approved closure → DONE
  | 'DONE'
  | 'CANCELED'

export type QuoteStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'REVISION_REQUESTED'
export type Urgency = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type VehicleCategory = 'CAR' | 'MOTORCYCLE' | 'TRUCK' | 'VAN' | 'BOAT' | 'OTHER'
export type FuelType = 'GASOLINE' | 'ETHANOL' | 'FLEX' | 'DIESEL' | 'ELECTRIC' | 'HYBRID' | 'GNV'
export type ItemType = 'PART' | 'LABOR' | 'OTHER'

// ── Client ────────────────────────────────────────────────
export interface Client {
  id: number
  name: string
  document: string
  phone?: string
  email?: string
  address?: string
  type?: string
  isActive: boolean
}

// ── Vehicle ───────────────────────────────────────────────
export interface Vehicle {
  id: number
  clientId: number
  plate: string
  renavam?: string
  chassis?: string
  brand: string
  model: string
  yearModel?: number
  yearManufacture?: number
  color?: string
  fuelType?: FuelType
  category: VehicleCategory
  usageType?: string
  mileageCurrent?: number
  ipvaValue?: number
  ipvaDueDate?: string
  licensingYear?: number
  licensingDueDate?: string
  licensingPaid?: boolean
  insurancePolicy?: string
  insuranceCompany?: string
  insuranceExpiry?: string
  insuranceValue?: number
  isActive: boolean
  notes?: string
  createdAt: string
  // computed
  client?: Client
  alertCount?: number
}

export interface VehicleCreate {
  clientId: number
  plate: string
  renavam?: string
  chassis?: string
  brand: string
  model: string
  yearModel?: number
  yearManufacture?: number
  color?: string
  fuelType?: FuelType
  category?: VehicleCategory
  usageType?: string
  mileageCurrent?: number
  ipvaValue?: number
  ipvaDueDate?: string
  licensingYear?: number
  licensingDueDate?: string
  licensingPaid?: boolean
  insurancePolicy?: string
  insuranceCompany?: string
  insuranceExpiry?: string
  insuranceValue?: number
  notes?: string
}

// ── Workshop ──────────────────────────────────────────────
export interface Workshop {
  id: number
  name: string
  cnpj?: string
  phone?: string
  email?: string
  address?: string
  city?: string
  state?: string
  contactName?: string
  specialties: string[]
  vehicleTypes: string[]
  rating?: number
  maxConcurrentOs?: number
  isActive: boolean
  notes?: string
  createdAt: string
}

// ── Fleet Request ─────────────────────────────────────────
export interface FleetRequest {
  id: number
  clientId: number
  vehicleId?: number
  boatId?: number
  problemDescription: string
  urgency: Urgency
  preferredDate?: string
  photos: string[]
  status: RequestStatus
  createdAt: string
  updatedAt: string
  // related
  client?: Client
  vehicle?: Vehicle
  quotes?: WorkshopQuote[]
  assignedWorkshops?: Workshop[]
}

// ── Quote ─────────────────────────────────────────────────
export interface QuoteItem {
  id?: number
  type: ItemType
  description: string
  partSku?: string
  quantity: number
  unitPrice: number
  total: number
  notes?: string
}

export interface WorkshopQuote {
  id: number
  fleetRequestId: number
  workshopId: number
  technicianName?: string
  diagnosis?: string
  estimatedDays?: number
  validityDays?: number
  subtotalParts: number
  subtotalLabor: number
  totalValue: number
  status: QuoteStatus
  rejectionReason?: string
  revisionNotes?: string
  photosBefore: string[]
  items: QuoteItem[]
  createdAt: string
  submittedAt?: string
  workshop?: Workshop
}

// ── Execution ─────────────────────────────────────────────
export interface WorkshopExecution {
  id: number
  quoteId: number
  fleetRequestId: number
  workshopId: number
  startedAt?: string
  completedAt?: string
  status: string
  technicianNotes?: string
  photosDuring: string[]
  photosAfter: string[]
  partsUsed: QuoteItem[]
  laborHours?: number
  totalExecuted?: number
  approvalStatus: 'PENDING' | 'ADMIN_APPROVED' | 'CLIENT_APPROVED' | 'APPROVED' | 'DISPUTED'
  disputeReason?: string
}

// ── Maintenance ───────────────────────────────────────────
export interface MaintenanceSchedule {
  id: number
  vehicleId?: number
  boatId?: number
  serviceType: string
  intervalKm?: number
  intervalDays?: number
  lastDoneAt?: string
  lastDoneKm?: number
  nextDueAt?: string
  nextDueKm?: number
  status: 'OK' | 'DUE_SOON' | 'OVERDUE'
  notes?: string
}
