import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Sidebar from '@/components/Sidebar';
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import SuperAdminDashboard from '@/pages/SuperAdminDashboard';
import OrganisationManagement from '@/pages/OrganisationManagement';
import BrandManagement from '@/pages/BrandManagement';
import ProductManagement from '@/pages/ProductManagement';
import OrganisationDashboardNew from '@/pages/OrganisationDashboardNew';
import OrganisationsPlatformManagement from '@/pages/OrganisationsPlatformManagement';
import OrganisationDetailView from '@/pages/OrganisationDetailView';
import SuperAdminCallLogs from '@/pages/SuperAdminCallLogs';
import KBGovernance from '@/pages/KBGovernance';
import OrganisationCompanies from '@/pages/OrganisationCompanies';
import OrganisationBrands from '@/pages/OrganisationBrands';
import OrganisationProducts from '@/pages/OrganisationProducts';
import OrganisationProfile from '@/pages/OrganisationProfile';
import OrganisationSettings from '@/pages/OrganisationSettings';
import OrganisationCallLogs from '@/pages/OrganisationCallLogs';
import CompanyBrands from '@/pages/CompanyBrands';
import CompanyProducts from '@/pages/CompanyProducts';
import CompanyDashboard from '@/pages/CompanyDashboard';
import CompanyProfile from '@/pages/CompanyProfile';
import CompanySettings from '@/pages/CompanySettings';
import CompanyCallLogs from '@/pages/CompanyCallLogs';
import SuperAdminCompanies from '@/pages/SuperAdminCompanies';
import SuperAdminCallAnalytics from '@/pages/SuperAdminCallAnalytics';
import SuperAdminAIManagement from '@/pages/SuperAdminAIManagement';
import PendingApprovals from '@/pages/PendingApprovals';
import OrganisationPendingApprovals from '@/pages/OrganisationPendingApprovals';
import SuperAdminSettings from '@/pages/SuperAdminSettings';
import ForgotPassword from '@/pages/ForgotPassword';
import ResetPassword from '@/pages/ResetPassword';

function AuthenticatedLayout({ children }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 pl-64">
        <main className="p-8 h-full bg-gray-50/30">{children}</main>
      </div>
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
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password/:token" element={<ResetPassword />} />

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
              path="/superadmin/pending-approvals"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <PendingApprovals />
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


            {/* Super Admin Platform Routes
            <Route
              path="/superadmin/platform"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <SuperAdminPlatformDashboard />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            /> */}


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
              path="/organisation/pending-approvals"
              element={
                <ProtectedRoute requiredRole="organisation">
                  <AuthenticatedLayout>
                    <OrganisationPendingApprovals />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/organisation/call-logs"
              element={
                <ProtectedRoute requiredRole="organisation">
                  <AuthenticatedLayout>
                    <OrganisationCallLogs />
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
            <Route
              path="/organisation/settings"
              element={
                <ProtectedRoute requiredRole="organisation">
                  <AuthenticatedLayout>
                    <OrganisationSettings />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/organisations"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AuthenticatedLayout>
                    <OrganisationManagement />
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
                    <CompanyProfile />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/company/call-logs"
              element={
                <ProtectedRoute requiredRole="company">
                  <AuthenticatedLayout>
                    <CompanyCallLogs />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/company/settings"
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
              path="/superadmin/call-logs"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <SuperAdminCallLogs />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            {/* <Route
              path="/superadmin/kb-governance"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <KBGovernance />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            /> */}
            <Route
              path="/superadmin/settings"
              element={
                <ProtectedRoute requiredRole="superadmin">
                  <AuthenticatedLayout>
                    <SuperAdminSettings />
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
