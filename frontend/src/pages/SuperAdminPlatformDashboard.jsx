// Enhanced Super Admin Platform Dashboard
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Package,
  Phone,
  PhoneCall,
  AlertTriangle,
  Users,
  TrendingUp,
  Activity,
  Settings,
  Shield,
  Database,
  BarChart3,
  Calendar,
  Filter,
  CheckCircle,
  Eye
} from 'lucide-react';
import api from '../api/api';

const SuperAdminPlatformDashboard = () => {
  const navigate = useNavigate();
  const [kpis, setKpis] = useState(null);
  const [organisations, setOrganisations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('today');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchKPIs();
    fetchOrganisations();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchKPIs(true);
      fetchOrganisations(true);
    }, 30000);
    return () => clearInterval(interval);
  }, [dateRange]);

  const fetchKPIs = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      else setRefreshing(true);
      
      const response = await api.get('/superadmin/dashboard/kpis');
      setKpis(response.data);
    } catch (error) {
      console.error('Error fetching KPIs:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchOrganisations = async (silent = false) => {
    try {
      const response = await api.get('/superadmin/organisations/stats');
      setOrganisations(response.data);
    } catch (error) {
      console.error('Error fetching organisations:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 font-medium">Loading Platform Dashboard...</p>
        </div>
      </div>
    );
  }

  const kpiCards = [
    {
      title: 'Total Organisations',
      value: kpis?.total_organisations || 0,
      subtitle: `${kpis?.active_organisations || 0} Active`,
      icon: Building2,
      color: 'bg-green-500',
      gradient: 'from-green-400 to-emerald-600',
      action: () => navigate('/superadmin/organisations-platform')
    },
    {
      title: 'Companies / Brands',
      value: kpis?.total_brands || 0,
      subtitle: `Across all orgs`,
      icon: Package,
      color: 'bg-green-600',
      gradient: 'from-green-500 to-emerald-700',
      action: () => navigate('/superadmin/brands')
    },
    {
      title: 'Active Phone Numbers',
      value: kpis?.active_phone_numbers || 0,
      subtitle: 'Multi-tenant routing',
      icon: Phone,
      color: 'bg-green-500',
      gradient: 'from-green-400 to-green-600',
      action: null
    },
    {
      title: 'Calls Today',
      value: kpis?.total_calls_today || 0,
      subtitle: `${kpis?.total_calls_month || 0} This Month`,
      icon: PhoneCall,
      color: 'bg-indigo-500',
      gradient: 'from-indigo-400 to-indigo-600',
      action: () => navigate('/superadmin/call-analytics')
    },
    {
      title: 'Live Calls',
      value: kpis?.live_calls_count || 0,
      subtitle: 'Active Right Now',
      icon: Activity,
      color: 'bg-red-500',
      gradient: 'from-red-400 to-red-600',
      action: () => navigate('/superadmin/live-calls'),
      pulse: (kpis?.live_calls_count || 0) > 0
    },
    {
      title: 'Escalated Cases',
      value: kpis?.escalated_cases_count || 0,
      subtitle: 'Pending Resolution',
      icon: AlertTriangle,
      color: 'bg-yellow-500',
      gradient: 'from-yellow-400 to-yellow-600',
      action: () => navigate('/superadmin/escalations')
    },
    {
      title: 'Avg AI Confidence',
      value: `${kpis?.avg_ai_confidence || 0}%`,
      subtitle: 'Platform-wide',
      icon: TrendingUp,
      color: 'bg-teal-500',
      gradient: 'from-teal-400 to-teal-600',
      action: null
    },
    {
      title: 'Total Users',
      value: kpis?.total_users || 0,
      subtitle: 'All Roles',
      icon: Users,
      color: 'bg-pink-500',
      gradient: 'from-pink-400 to-pink-600',
      action: () => navigate('/superadmin/users')
    },
    {
      title: 'KB Entries',
      value: kpis?.total_kb_entries || 0,
      subtitle: 'Knowledge Base',
      icon: Database,
      color: 'bg-cyan-500',
      gradient: 'from-cyan-400 to-cyan-600',
      action: () => navigate('/superadmin/kb-governance')
    },
  ];

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
              <Shield className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Super Admin Platform</h1>
              <p className="text-gray-600 mt-1 text-lg">National-scale Multi-tenant SaaS Control Center</p>
            </div>
          </div>
        </div>
        
        <div className="flex gap-3">
          {refreshing && (
            <div className="flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-lg">
              <Activity className="h-4 w-4 animate-spin" />
              <span className="text-sm font-medium">Refreshing...</span>
            </div>
          )}
          <button
            onClick={() => navigate('/superadmin/platform-settings')}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 shadow-md transition-all"
          >
            <Settings className="h-4 w-4" />
            Platform Settings
          </button>
          <button
            onClick={() => navigate('/superadmin/audit-logs')}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 shadow-md transition-all"
          >
            <BarChart3 className="h-4 w-4" />
            Audit Logs
          </button>
        </div>
      </div>

      {/* Date Range Filter */}
      <div className="bg-white rounded-xl shadow-md p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Calendar className="h-5 w-5 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">Date Range:</span>
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="quarter">This Quarter</option>
            <option value="all">All Time</option>
          </select>
        </div>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {kpiCards.map((card, index) => (
          <div
            key={index}
            onClick={card.action}
            className={`bg-white rounded-xl shadow-lg overflow-hidden transform transition-all duration-300 hover:scale-105 ${
              card.action ? 'cursor-pointer hover:shadow-2xl' : ''
            } ${card.pulse ? 'ring-4 ring-red-300 animate-pulse' : ''}`}
          >
            <div className={`h-2 bg-gradient-to-r ${card.gradient}`}></div>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 bg-gradient-to-br ${card.gradient} rounded-lg shadow-md`}>
                  <card.icon className="h-6 w-6 text-white" />
                </div>
                {card.pulse && (
                  <span className="px-3 py-1 bg-red-100 text-red-700 text-xs font-bold rounded-full animate-pulse">
                    LIVE
                  </span>
                )}
              </div>
              <h3 className="text-gray-600 text-sm font-medium mb-1">{card.title}</h3>
              <p className="text-4xl font-bold text-gray-900 mb-2">{card.value}</p>
              <p className="text-gray-500 text-sm">{card.subtitle}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Organisation Phone Numbers */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Phone className="h-6 w-6 text-green-600" />
            Active Phone Numbers by Organisation
          </h2>
          <span className="text-sm text-gray-500">AI connects on these numbers</span>
        </div>
        
        {kpis?.active_phone_numbers === 0 ? (
          <div className="text-center py-8 bg-gray-50 rounded-lg">
            <Phone className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-600">No phone numbers configured yet</p>
            <p className="text-sm text-gray-500 mt-1">Configure phone numbers for organisations to enable AI voice advisory</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {organisations
              .filter(org => org.phone_count > 0)
              .map(org => (
                <div key={org.id} className="p-4 bg-green-50 border-l-4 border-green-500 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-5 w-5 text-green-600" />
                      <h3 className="font-bold text-gray-900">{org.name}</h3>
                    </div>
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${
                      org.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {org.is_active ? 'Active' : 'Suspended'}
                    </span>
                  </div>
                  <div className="space-y-1 mt-3">
                    {org.phone_numbers.map((phone, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-sm">
                        <Phone className="h-4 w-4 text-green-600" />
                        <span className="font-mono text-gray-900">{phone}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 pt-3 border-t border-green-200 flex justify-between text-xs text-gray-600">
                    <span>{org.brand_count} Brands • {org.product_count} Products</span>
                    <span>{org.call_count} Calls Total</span>
                  </div>
                  <button
                    onClick={() => navigate(`/superadmin/organisations-platform/${org.id}`)}
                    className="mt-3 w-full px-3 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-all flex items-center justify-center gap-2"
                  >
                    <Eye className="h-4 w-4" />
                    View Details
                  </button>
                </div>
              ))}
          </div>
        )}
        
        <div className="mt-4 p-3 bg-yellow-50 border-l-4 border-yellow-500 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div className="text-sm">
              <p className="text-yellow-800 font-semibold mb-1">🎯 How it works:</p>
              <p className="text-yellow-700">
                When farmers call these numbers → AI identifies organisation → Loads their brands & products → Provides voice advisory
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Platform Management</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => navigate('/superadmin/organisations-platform')}
            className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-all"
          >
            <Building2 className="h-6 w-6 text-indigo-600" />
            <div className="text-left">
              <div className="font-medium text-gray-900">Organisations</div>
              <div className="text-xs text-gray-500">Manage all tenants</div>
            </div>
          </button>

          <button
            onClick={() => navigate('/superadmin/kb-governance')}
            className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all"
          >
            <Database className="h-6 w-6 text-green-600" />
            <div className="text-left">
              <div className="font-medium text-gray-900">KB Governance</div>
              <div className="text-xs text-gray-500">Approve entries</div>
            </div>
          </button>

          <button
            onClick={() => navigate('/superadmin/product-safety')}
            className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-red-500 hover:bg-red-50 transition-all"
          >
            <Shield className="h-6 w-6 text-red-600" />
            <div className="text-left">
              <div className="font-medium text-gray-900">Product Safety</div>
              <div className="text-xs text-gray-500">Ban products</div>
            </div>
          </button>

          <button
            onClick={() => navigate('/superadmin/call-analytics')}
            className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all"
          >
            <BarChart3 className="h-6 w-6 text-purple-600" />
            <div className="text-left">
              <div className="font-medium text-gray-900">Call Analytics</div>
              <div className="text-xs text-gray-500">Platform insights</div>
            </div>
          </button>
        </div>
      </div>

      {/* System Health Warning */}
      {(kpis?.escalated_cases_count > 10 || kpis?.avg_ai_confidence < 60) && (
        <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-6">
          <div className="flex items-start">
            <AlertTriangle className="h-6 w-6 text-red-600 mr-3 mt-0.5" />
            <div>
              <h3 className="text-red-800 font-bold text-lg mb-2">System Health Alert</h3>
              <ul className="text-red-700 space-y-1">
                {kpis?.escalated_cases_count > 10 && (
                  <li>• High escalation count ({kpis.escalated_cases_count}) - requires attention</li>
                )}
                {kpis?.avg_ai_confidence < 60 && (
                  <li>• Low AI confidence ({kpis.avg_ai_confidence}%) - review RAG settings</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SuperAdminPlatformDashboard;
