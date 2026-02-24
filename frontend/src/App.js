import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Sidebar from '@/components/Sidebar';
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import Dashboard from '@/pages/Dashboard';
import CallHistory from '@/pages/CallHistory';
import KnowledgeBase from '@/pages/KnowledgeBase';
import Escalations from '@/pages/Escalations';
import Profile from '@/pages/Profile';
import SuperAdminDashboard from '@/pages/SuperAdminDashboard';
import UserManagement from '@/pages/UserManagement';
import OrganisationManagement from '@/pages/OrganisationManagement';
import BrandManagement from '@/pages/BrandManagement';
import ProductManagement from '@/pages/ProductManagement';
import RasiSeedsJourney from '@/pages/RasiSeedsJourney';
import OrganisationDashboard from '@/pages/OrganisationDashboard';
import OrganisationBrands from '@/pages/OrganisationBrands';
import OrganisationProducts from '@/pages/OrganisationProducts';
import OrganisationProfile from '@/pages/OrganisationProfile';
import OrganisationSettings from '@/pages/OrganisationSettings';
import SuperAdminPlatformDashboard from '@/pages/SuperAdminPlatformDashboard';
import OrganisationsPlatformManagement from '@/pages/OrganisationsPlatformManagement';
import OrganisationDetailView from '@/pages/OrganisationDetailView';
import ProductSafetyControl from '@/pages/ProductSafetyControl';
import AuditLogsViewer from '@/pages/AuditLogsViewer';
import KBGovernance from '@/pages/KBGovernance';
import AdminOrganisations from '@/pages/AdminOrganisations';
import OrganisationCompanies from '@/pages/OrganisationCompanies';
import CompanyBrands from '@/pages/CompanyBrands';
import CompanyProducts from '@/pages/CompanyProducts';
import CompanyDashboard from '@/pages/CompanyDashboard';
import CompanySettings from '@/pages/CompanySettings';
import AdminSettings from '@/pages/AdminSettings';
import OrganisationDashboardNew from '@/pages/OrganisationDashboardNew';
import SuperAdminCompanies from '@/pages/SuperAdminCompanies';
import SuperAdminCallAnalytics from '@/pages/SuperAdminCallAnalytics';
import SuperAdminAIManagement from '@/pages/SuperAdminAIManagement';
import '@/App.css';

function AuthenticatedLayout({ children }) {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 ml-64 p-8">{children}</main>
    </div>
  );
}

function App() {
  return (
    <div className="App bg-background min-h-screen">
      <Toaster position="top-right" />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <AuthenticatedLayout>
                    <Dashboard />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/calls"
              element={
                <ProtectedRoute>
                  <AuthenticatedLayout>
                    <CallHistory />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/knowledge-base"
              element={
                <ProtectedRoute>
                  <AuthenticatedLayout>
                    <KnowledgeBase />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/escalations"
              element={
                <ProtectedRoute>
                  <AuthenticatedLayout>
                    <Escalations />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <AuthenticatedLayout>
                    <Profile />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/farmers"
              element={
                <ProtectedRoute>
                  <AuthenticatedLayout>
                    <div data-testid="farmers-page" className="text-2xl">
                      Farmers Page - Coming Soon
                    </div>
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/cases"
              element={
                <ProtectedRoute>
                  <AuthenticatedLayout>
                    <div data-testid="cases-page" className="text-2xl">
                      Cases Page - Coming Soon
                    </div>
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <AuthenticatedLayout>
                    <AdminSettings />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/superadmin"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <SuperAdminDashboard />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/superadmin/users"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <UserManagement />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/superadmin/organisations"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <OrganisationManagement />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/superadmin/brands"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <BrandManagement />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/superadmin/products"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <ProductManagement />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/superadmin/companies"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <SuperAdminCompanies />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/superadmin/call-analytics"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <SuperAdminCallAnalytics />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/superadmin/ai-management"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <SuperAdminAIManagement />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/rasi-seeds-journey"
              element={
                <ProtectedRoute>
                  <AuthenticatedLayout>
                    <RasiSeedsJourney />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />

            {/* Organisation Admin Routes */}
            <Route
              path="/org-admin"
              element={
                <ProtectedRoute requiredRole="organisation_admin">
                  <AuthenticatedLayout>
                    <OrganisationDashboard />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/org-admin/brands"
              element={
                <ProtectedRoute requiredRole="organisation_admin">
                  <AuthenticatedLayout>
                    <OrganisationBrands />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/org-admin/products"
              element={
                <ProtectedRoute requiredRole="organisation_admin">
                  <AuthenticatedLayout>
                    <OrganisationProducts />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/org-admin/profile"
              element={
                <ProtectedRoute requiredRole="organisation_admin">
                  <AuthenticatedLayout>
                    <OrganisationProfile />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/org-admin/settings"
              element={
                <ProtectedRoute requiredRole="organisation_admin">
                  <AuthenticatedLayout>
                    <OrganisationSettings />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />

            {/* Super Admin Platform Routes */}
            <Route
              path="/superadmin/platform"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <SuperAdminPlatformDashboard />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            
            {/* Admin Routes - Organisation Management */}
            <Route
              path="/admin/organisations"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AuthenticatedLayout>
                    <AdminOrganisations />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />

            {/* Organisation Role Routes */}
            <Route
              path="/organisation/dashboard"
              element={
                <ProtectedRoute requiredRole="organisation">
                  <AuthenticatedLayout>
                    <OrganisationDashboardNew />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/organisation/companies"
              element={
                <ProtectedRoute requiredRole="organisation">
                  <AuthenticatedLayout>
                    <OrganisationCompanies />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/organisation/brands"
              element={
                <ProtectedRoute requiredRole="organisation">
                  <AuthenticatedLayout>
                    <OrganisationBrands />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/organisation/products"
              element={
                <ProtectedRoute requiredRole="organisation">
                  <AuthenticatedLayout>
                    <OrganisationProducts />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/organisation/profile"
              element={
                <ProtectedRoute requiredRole="organisation">
                  <AuthenticatedLayout>
                    <OrganisationProfile />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            
            {/* Company Role Routes */}
            <Route
              path="/company/dashboard"
              element={
                <ProtectedRoute requiredRole="company">
                  <AuthenticatedLayout>
                    <CompanyDashboard />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/company/brands"
              element={
                <ProtectedRoute requiredRole="company">
                  <AuthenticatedLayout>
                    <CompanyBrands />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/company/products"
              element={
                <ProtectedRoute requiredRole="company">
                  <AuthenticatedLayout>
                    <CompanyProducts />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/company/profile"
              element={
                <ProtectedRoute requiredRole="company">
                  <AuthenticatedLayout>
                    <CompanySettings />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            
            {/* Super Admin Platform Routes */}
            <Route
              path="/superadmin/organisations-platform"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <OrganisationsPlatformManagement />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/superadmin/organisations-platform/:orgId"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <OrganisationDetailView />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/superadmin/product-safety"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <ProductSafetyControl />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/superadmin/audit-logs"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <AuditLogsViewer />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />            <Route
              path="/superadmin/kb-governance"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <KBGovernance />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            {/* Redirect root to login */}
            <Route path="/" element={<Navigate to="/login" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
