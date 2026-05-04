import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import PrivateRoute from '@shared/components/PrivateRoute'

// Layouts
import AdminLayout from '@portals/admin/AdminLayout'
import ClientLayout from '@portals/client/ClientLayout'
import WorkshopLayout from '@portals/workshop/WorkshopLayout'

// Auth
const LoginPage = lazy(() => import('@portals/auth/LoginPage'))

// Admin portal pages
const AdminDashboard   = lazy(() => import('@portals/admin/dashboard/DashboardPage'))
const VehiclesPage     = lazy(() => import('@portals/admin/vehicles/VehiclesPage'))
const VehicleDetailPage = lazy(() => import('@portals/admin/vehicles/VehicleDetailPage'))
const BoatsFleetPage   = lazy(() => import('@portals/admin/boats/BoatsFleetPage'))
const BoatDetailPage   = lazy(() => import('@portals/admin/boats/BoatDetailPage'))
const ClientsPage      = lazy(() => import('@portals/admin/clients/ClientsPage'))
const ClientDetailPage  = lazy(() => import('@portals/admin/clients/ClientDetailPage'))
const WorkshopsPage    = lazy(() => import('@portals/admin/workshops/WorkshopsPage'))
const AdminRequestsPage = lazy(() => import('@portals/admin/requests/RequestsPage'))
const CatalogPage      = lazy(() => import('@portals/admin/catalog/CatalogPage'))
const PreventiveRulesPage = lazy(() => import('@portals/admin/schedule/PreventiveRulesPage'))
const ReportsPage      = lazy(() => import('@portals/admin/reports/ReportsPage'))
const SettingsPage     = lazy(() => import('@portals/admin/settings/SettingsPage'))
const AlertsCenterPage = lazy(() => import('@portals/admin/dashboard/AlertsCenterPage'))

// Client portal pages
const ClientDashboard  = lazy(() => import('@portals/client/dashboard/DashboardPage'))
const MyFleetPage      = lazy(() => import('@portals/client/fleet/MyFleetPage'))
const ClientRequestsPage = lazy(() => import('@portals/client/requests/RequestsPage'))
const NewRequestPage   = lazy(() => import('@portals/client/requests/NewRequestPage'))
const RequestDetailClientPage = lazy(() => import('@portals/client/requests/RequestDetailPage'))
const AssetDetailPage      = lazy(() => import('@portals/client/fleet/AssetDetailPage'))
const ClientAssetHistoryPage = lazy(() => import('@portals/client/fleet/ClientAssetHistoryPage'))

// Workshop portal pages
const WorkshopDashboard = lazy(() => import('@portals/workshop/dashboard/DashboardPage'))
const WorkshopRequestsPage = lazy(() => import('@portals/workshop/requests/RequestsPage'))
const QuoteBuilderPage  = lazy(() => import('@portals/workshop/quotes/QuoteBuilderPage'))
const ExecutionPage     = lazy(() => import('@portals/workshop/execution/ExecutionPage'))
const WorkshopExecutionDetail = lazy(() => import('@portals/workshop/execution/WorkshopExecutionDetail'))

const ADMIN_ROLES = ['ADMIN', 'MANAGER', 'TECHNICIAN'] as const

const Loader = () => (
  <div className="flex items-center justify-center h-64">
    <div className="w-8 h-8 rounded-full border-2 border-amber-500 border-t-transparent animate-spin" />
  </div>
)

export default function App() {
  return (
    <BrowserRouter basename="/fleet_os">
      <Suspense fallback={<Loader />}>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* Admin Portal */}
          <Route element={<PrivateRoute allowedRoles={[...ADMIN_ROLES]} />}>
            <Route element={<AdminLayout />}>
              <Route path="/admin/dashboard"  element={<AdminDashboard />} />
              <Route path="/admin/vehicles"   element={<VehiclesPage />} />
              <Route path="/admin/vehicles/:id" element={<VehicleDetailPage />} />
              <Route path="/admin/boats"      element={<BoatsFleetPage />} />
              <Route path="/admin/boats/:id"  element={<BoatDetailPage />} />
              <Route path="/admin/clients"     element={<ClientsPage />} />
              <Route path="/admin/clients/:id" element={<ClientDetailPage />} />
              <Route path="/admin/workshops"  element={<WorkshopsPage />} />
              <Route path="/admin/requests"   element={<AdminRequestsPage />} />
              <Route path="/admin/catalog"    element={<CatalogPage />} />
              <Route path="/admin/schedule"   element={<PreventiveRulesPage />} />
              <Route path="/admin/reports"    element={<ReportsPage />} />
              <Route path="/admin/settings"   element={<SettingsPage />} />
              <Route path="/admin/alerts"     element={<AlertsCenterPage />} />
            </Route>
          </Route>

          {/* Client Portal */}
          <Route element={<PrivateRoute allowedRoles={['CLIENT']} />}>
            <Route element={<ClientLayout />}>
              <Route path="/client/dashboard"        element={<ClientDashboard />} />
              <Route path="/client/my-fleet"         element={<MyFleetPage />} />
              <Route path="/client/requests"         element={<ClientRequestsPage />} />
              <Route path="/client/requests/new"     element={<NewRequestPage />} />
              <Route path="/client/requests/:id"     element={<RequestDetailClientPage />} />
              <Route path="/client/fleet/:id"        element={<AssetDetailPage />} />
              <Route path="/client/fleet/:id/history" element={<ClientAssetHistoryPage />} />
            </Route>
          </Route>

          {/* Workshop Portal */}
          <Route element={<PrivateRoute allowedRoles={['PARTNER']} />}>
            <Route element={<WorkshopLayout />}>
              <Route path="/workshop/dashboard"          element={<WorkshopDashboard />} />
              <Route path="/workshop/requests"           element={<WorkshopRequestsPage />} />
              <Route path="/workshop/requests/:id/quote" element={<QuoteBuilderPage />} />
              <Route path="/workshop/execution"          element={<ExecutionPage />} />
              <Route path="/workshop/execution/:id"      element={<WorkshopExecutionDetail />} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
