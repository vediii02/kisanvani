import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Phone, Users, FileText, AlertTriangle, Database, Settings, LogOut, User, Shield, UserCog, Building2, Package, Tag, BarChart3, Brain, Globe, Clock } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export default function Sidebar() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  // Only show generic dashboard for supervisor (not admin/superadmin/company)
  const menuItems = [
    ...(user?.role === 'supervisor' ? [
      { path: '/superadmin', icon: LayoutDashboard, label: 'Dashboard', testid: 'nav-dashboard' },
    ] : []),
    { path: '/calls', icon: Phone, label: 'Call History', testid: 'nav-calls' },
    { path: '/farmers', icon: Users, label: 'Farmers', testid: 'nav-farmers' },
    { path: '/cases', icon: FileText, label: 'Cases', testid: 'nav-cases' },
    { path: '/escalations', icon: AlertTriangle, label: 'Escalations', testid: 'nav-escalations' },
    { path: '/knowledge-base', icon: Database, label: 'Knowledge Base', testid: 'nav-kb' },
    { path: '/profile', icon: User, label: 'Profile', testid: 'nav-profile' },
    { path: '/settings', icon: Settings, label: 'Settings', testid: 'nav-settings' },
  ];

  const adminItems = [
    // { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', testid: 'nav-admin-main-dashboard' },
    { path: '/superadmin', icon: Shield, label: 'Admin Dashboard', testid: 'nav-admin-dashboard' },
    { path: '/superadmin/pending-approvals', icon: Clock, label: 'Pending Approvals', testid: 'nav-admin-pending' },
    // { path: '/superadmin/users', icon: UserCog, label: 'User Management', testid: 'nav-admin-users' },
    { path: '/superadmin/organisations-platform', icon: Building2, label: 'Organisation', testid: 'nav-admin-org-platform' },
    { path: '/superadmin/companies', icon: Building2, label: 'Companies', testid: 'nav-admin-companies' },
    { path: '/superadmin/brands', icon: Tag, label: 'Brands', testid: 'nav-admin-brands' },
    { path: '/superadmin/products', icon: Package, label: 'Products', testid: 'nav-admin-products' },
    // { path: '/superadmin/platform', icon: Globe, label: 'Platform Dashboard', testid: 'nav-admin-platform' },
    { path: '/superadmin/call-logs', icon: Phone, label: 'Call Logs', testid: 'nav-admin-audit' },
    { path: '/superadmin/call-analytics', icon: BarChart3, label: 'Call Analytics', testid: 'nav-admin-analytics' },
    { path: '/superadmin/ai-management', icon: Brain, label: 'AI Management', testid: 'nav-admin-ai' },

    // { path: '/superadmin/product-safety', icon: AlertTriangle, label: 'Product Safety', testid: 'nav-admin-safety' },
    // { path: '/superadmin/kb-governance', icon: Database, label: 'KB Governance', testid: 'nav-admin-kb' },
    { path: '/superadmin/settings', icon: Settings, label: 'Settings', testid: 'nav-admin-settings' },
  ];

  const organisationItems = [
    { path: '/organisation/dashboard', icon: LayoutDashboard, label: 'Dashboard', testid: 'nav-org-dashboard' },
    { path: '/organisation/pending-approvals', icon: Clock, label: 'Pending Approvals', testid: 'nav-org-pending' },
    { path: '/organisation/companies', icon: Building2, label: 'Companies', testid: 'nav-org-companies' },
    { path: '/organisation/brands', icon: Tag, label: 'Brands', testid: 'nav-org-brands' },
    { path: '/organisation/products', icon: Package, label: 'Products', testid: 'nav-org-products' },
    { path: '/organisation/call-logs', icon: Phone, label: 'Call Logs', testid: 'nav-org-calls' },
    { path: '/organisation/profile', icon: User, label: 'Profile', testid: 'nav-org-profile' },
    { path: '/organisation/settings', icon: Settings, label: 'Settings', testid: 'nav-org-settings' },
  ];

  const companyItems = [
    { path: '/company/dashboard', icon: LayoutDashboard, label: 'Dashboard', testid: 'nav-company-dashboard' },
    { path: '/company/brands', icon: Tag, label: 'My Brands', testid: 'nav-company-brands' },
    { path: '/company/products', icon: Package, label: 'My Products', testid: 'nav-company-products' },
    { path: '/company/call-logs', icon: Phone, label: 'Call Logs', testid: 'nav-company-calls' },
    { path: '/company/profile', icon: User, label: 'Profile', testid: 'nav-company-profile' },
    { path: '/company/settings', icon: Settings, label: 'Settings', testid: 'nav-company-settings' },
  ];

  return (
    <aside className="w-64 bg-primary text-primary-foreground h-screen fixed left-0 top-0 shadow-lg flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold tracking-tight" data-testid="app-title">Kisan Vani AI</h1>
        <p className="text-sm opacity-80 mt-1">Voice Advisory Platform</p>
      </div>

      <nav className="px-3 mt-4 flex-1 overflow-y-auto scrollbar-hide">
        {user?.role === 'supervisor' && menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              data-testid={item.testid}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-md mb-2 transition-colors ${isActive ? 'bg-primary-foreground/20 font-medium' : 'hover:bg-primary-foreground/10'
                }`
              }
            >
              <Icon className="w-5 h-5" strokeWidth={1.5} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}

        {(user?.role === 'admin' || user?.role === 'superadmin') && (
          <>
            <div className="mb-2 px-4 text-xs opacity-70 font-medium uppercase tracking-wider">
              Admin Panel
            </div>
            {adminItems.filter(item => item.path !== '/dashboard').map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  data-testid={item.testid}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-md mb-2 transition-colors ${isActive ? 'bg-primary-foreground/20 font-medium' : 'hover:bg-primary-foreground/10'
                    }`
                  }
                >
                  <Icon className="w-5 h-5" strokeWidth={1.5} />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </>
        )}

        {(user?.role === 'organisation' || user?.role === 'organisation_admin') && (
          <>
            <div className="my-4 px-4">
              <div className="h-px bg-primary-foreground/20"></div>
            </div>
            <div className="mb-2 px-4 text-xs opacity-70 font-medium uppercase tracking-wider">
              Organisation Management
            </div>
            {organisationItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  data-testid={item.testid}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-md mb-2 transition-colors ${isActive ? 'bg-primary-foreground/20 font-medium' : 'hover:bg-primary-foreground/10'
                    }`
                  }
                >
                  <Icon className="w-5 h-5" strokeWidth={1.5} />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </>
        )}

        {user?.role === 'company' && (
          <>
            <div className="mb-2 px-4 text-xs opacity-70 font-medium uppercase tracking-wider">
              Company Management
            </div>
            {companyItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  data-testid={item.testid}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-md mb-2 transition-colors ${isActive ? 'bg-primary-foreground/20 font-medium' : 'hover:bg-primary-foreground/10'
                    }`
                  }
                >
                  <Icon className="w-5 h-5" strokeWidth={1.5} />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </>
        )}
      </nav>

      <div className="p-4 border-t border-primary-foreground/20">
        <div className="mb-3 px-2">
          <p className="text-xs opacity-70">Logged in as</p>
          <p className="text-sm font-medium" data-testid="sidebar-username">{user?.username}</p>
          <p className="text-xs opacity-70 capitalize">{user?.role}</p>
        </div>
        <Button
          onClick={handleLogout}
          data-testid="logout-btn"
          variant="ghost"
          className="w-full justify-start text-primary-foreground hover:bg-primary-foreground/10"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Logout
        </Button>
      </div>
    </aside>
  );
}
