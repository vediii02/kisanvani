import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Package,
  Phone,
  PhoneCall,
  AlertTriangle,
  Users,
  UserCheck,
  UserX,
  UserCog,
  Activity,
  Shield,
  BarChart3,
  Calendar,
  Eye,
  Loader2,
  LayoutDashboard
} from 'lucide-react';
import api, { superAdminAPI } from '../api/api';

export default function SuperAdminDashboard() {
  const navigate = useNavigate();
  const [kpis, setKpis] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [organisations, setOrganisations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('today');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchAllData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchAllData(true);
    }, 30000);
    return () => clearInterval(interval);
  }, [dateRange]);

  const fetchAllData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      else setRefreshing(true);

      const [kpiRes, statsRes, orgsRes] = await Promise.all([
        api.get('/superadmin/dashboard/kpis'),
        api.get('/superadmin/dashboard/stats'),
        api.get('/superadmin/organisations/stats')
      ]);

      setKpis(kpiRes.data);
      setUserStats(statsRes.data);
      setOrganisations(orgsRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-indigo-600 mx-auto" />
          <p className="mt-4 text-gray-600 font-medium">Loading Platform Dashboard...</p>
        </div>
      </div>
    );
  }

  const platformCards = [
    {
      title: 'Organisations',
      value: kpis?.total_organisations || 0,
      subtitle: `${kpis?.active_organisations || 0} Active`,
      icon: Building2,
      gradient: 'from-green-400 to-emerald-600',
      action: () => navigate('/superadmin/organisations-platform')
    },
    {
      title: 'Total Companies',
      value: kpis?.total_companies || 0,
      subtitle: `${kpis?.total_companies || 0} Companies`,
      icon: Building2,
      gradient: 'from-emerald-500 to-teal-700',
      action: () => navigate('/superadmin/companies')
    },
    {
      title: 'Total Brands',
      value: kpis?.total_brands || 0,
      subtitle: `${kpis?.total_brands || 0} Brands`,
      icon: Package,
      gradient: 'from-indigo-500 to-purple-700',
      action: () => navigate('/superadmin/brands')
    },
    {
      title: 'Total Products',
      value: kpis?.total_products || 0,
      subtitle: `${kpis?.total_products || 0} Products`,
      icon: Package,
      gradient: 'from-indigo-500 to-purple-700',
      action: () => navigate('/superadmin/products')
    },
  ];

  const userCards = [
    {
      title: 'Total Users',
      value: userStats?.total_users || 0,
      subtitle: 'Platform Wide',
      icon: Users,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
      action: null
    },
    {
      title: 'Active Users',
      value: userStats?.active_users || 0,
      subtitle: 'Access Enabled',
      icon: UserCheck,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      action: null
    },
    {
      title: 'Inactive Users',
      value: userStats?.inactive_users || 0,
      subtitle: 'Access Blocked',
      icon: UserX,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      action: null
    },
    {
      title: 'Org Admins',
      value: userStats?.total_admins || 0,
      subtitle: 'Tenant Controllers',
      icon: UserCog,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      action: null
    },
    {
      title: 'Company Users',
      value: userStats?.total_company_users || 0,
      subtitle: 'Branch Controllers',
      icon: UserCog,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      action: null
    }
  ];

  const monitoringCards = [
    {
      title: 'Live Calls',
      value: kpis?.live_calls_count || 0,
      subtitle: 'Active Right Now',
      icon: Activity,
      gradient: 'from-red-400 to-red-600',
      action: null,
      pulse: (kpis?.live_calls_count || 0) > 0
    },
    {
      title: 'Calls Today',
      value: kpis?.total_calls_today || 0,
      subtitle: `${kpis?.total_calls_month || 0} This Month`,
      icon: PhoneCall,
      gradient: 'from-indigo-400 to-indigo-600',
      action: () => navigate('/superadmin/call-analytics')
    },
    {
      title: 'Avg Confidence',
      value: `${kpis?.avg_ai_confidence || 0}%`,
      subtitle: 'AI Precision',
      icon: Shield,
      gradient: 'from-amber-400 to-orange-600',
      action: null
    }
  ];

  return (
    <div className="p-6 space-y-8 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br rounded-xl bg-green-800 shadow-lg">
              <Shield className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold flex items-center gap-2 text-gray-900 tracking-tight">
                Super Admin Platform
              </h1>
              <p className="text-gray-600 mt-1 text-lg">National-scale Multi-tenant SaaS Control Center</p>
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          {refreshing && (
            <div className="flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-lg animate-fade-in">
              <Activity className="h-4 w-4 animate-spin" />
              <span className="text-sm font-medium">Refreshing...</span>
            </div>
          )}
          <button
            onClick={() => navigate('/superadmin/call-logs')}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 shadow-md transition-all font-medium"
          >
            <BarChart3 className="h-4 w-4" />
            Call Logs
          </button>
        </div>
      </div>

      {/* 1. Platform Overview Tier */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <Building2 className="h-5 w-5 text-indigo-600" />
          Platform Hierarchy
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {platformCards.map((card, index) => (
            <div
              key={index}
              onClick={card.action}
              className={`bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden transform transition-all duration-300 hover:scale-[1.02] ${card.action ? 'cursor-pointer hover:shadow-xl' : ''}`}
            >
              <div className={`h-1.5 bg-gradient-to-r ${card.gradient}`}></div>
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 bg-gradient-to-br ${card.gradient} rounded-lg shadow-sm text-white`}>
                    <card.icon className="h-6 w-6" />
                  </div>
                </div>
                <h3 className="text-gray-500 text-xs font-bold uppercase tracking-wider mb-1">{card.title}</h3>
                <p className="text-3xl font-black text-gray-900 mb-1 tabular-nums">{card.value}</p>
                <p className="text-gray-500 text-xs font-semibold">{card.subtitle}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 2. User Ecosystem Tier (RESTORED STATS) */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <Users className="h-5 w-5 text-blue-600" />
          User Ecosystem & Governance
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {userCards.map((card, index) => {
            const Icon = card.icon;
            return (
              <div
                key={index}
                onClick={card.action}
                className={`bg-white p-5 rounded-xl border border-gray-200 shadow-sm transition-all hover:border-blue-300 ${card.action ? 'cursor-pointer' : ''}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className={`p-2 rounded-lg ${card.bgColor}`}>
                    <Icon className={`w-5 h-5 ${card.color}`} />
                  </div>
                </div>
                <div>
                  <p className="text-xs font-bold text-gray-500 uppercase tracking-tight">{card.title}</p>
                  <p className="text-2xl font-black text-gray-900 mt-1">{card.value}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 3. Monitoring Tier */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <Activity className="h-5 w-5 text-red-600" />
          Real-time Operations
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {monitoringCards.map((card, index) => (
            <div
              key={index}
              onClick={card.action}
              className={`bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden transform transition-all duration-300 hover:scale-[1.02] ${card.action ? 'cursor-pointer hover:shadow-xl' : ''
                } ${card.pulse ? 'ring-2 ring-red-500 ring-offset-2' : ''}`}
            >
              <div className={`h-1.5 bg-gradient-to-r ${card.gradient}`}></div>
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 bg-gradient-to-br ${card.gradient} rounded-lg shadow-sm text-white`}>
                    <card.icon className="h-6 w-6" />
                  </div>
                  {card.pulse && (
                    <span className="flex items-center gap-1.5 px-3 py-1 bg-red-100 text-red-700 text-xs font-black rounded-full animate-pulse">
                      <span className="h-2 w-2 rounded-full bg-red-600"></span>
                      LIVE
                    </span>
                  )}
                </div>
                <h3 className="text-gray-500 text-xs font-bold uppercase tracking-wider mb-1">{card.title}</h3>
                <p className="text-3xl font-black text-gray-900 mb-1 tabular-nums">{card.value}</p>
                <p className="text-gray-500 text-xs font-semibold">{card.subtitle}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Advisory Lines Grid */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Phone className="h-5 w-5 text-green-600" />
            Active Advisory Lines
          </h2>
        </div>

        {!organisations || organisations.every(org => org.phone_count === 0) ? (
          <div className="text-center py-12 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
            <Phone className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-900 font-bold text-lg">No advisory lines configured</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {organisations
              .filter(org => org.phone_count > 0)
              .map(org => (
                <div key={org.id} className="bg-white border border-gray-200 rounded-xl p-5 hover:border-green-500 hover:shadow-lg transition-all group">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center">
                        <Building2 className="h-5 w-5 text-indigo-600" />
                      </div>
                      <h3 className="font-bold text-gray-900">{org.name}</h3>
                    </div>
                    <span className={`px-2 py-0.5 text-[10px] font-black rounded ${org.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {org.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </div>

                  <div className="space-y-1 mb-4">
                    {org.phone_numbers && (typeof org.phone_numbers === 'string' ? org.phone_numbers.split(',') : org.phone_numbers).map((phone, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs font-mono font-bold text-gray-700 bg-gray-50 p-1.5 rounded">
                        <Phone className="h-3 w-3 text-green-600" />
                        {phone.trim()}
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center justify-between text-[10px] font-bold text-gray-500 pb-3 border-b mb-3">
                    <span>{org.product_count} SKUS</span>
                    <span>{org.call_count} CALLS</span>
                  </div>

                  <button
                    onClick={() => navigate(`/superadmin/organisations-platform/${org.id}`)}
                    className="w-full py-2 bg-gray-900 text-white rounded-lg text-xs font-bold hover:bg-indigo-600 transition-all flex items-center justify-center gap-2"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    INSPECT TENANT
                  </button>
                </div>
              ))}
          </div>
        )}
      </section>

      {/* Health Alerts */}
      {(kpis?.escalated_cases_count > 10 || kpis?.avg_ai_confidence < 60) && (
        <div className="bg-white border-2 border-red-100 rounded-xl p-6 shadow-md ring-4 ring-red-50 ring-inset">
          <div className="flex items-start">
            <AlertTriangle className="h-8 w-8 text-red-600 mr-4 mt-1 animate-bounce" />
            <div className="flex-1">
              <h3 className="text-red-900 font-black text-xl mb-3 uppercase tracking-tighter">Platform Anomalies Detected</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {kpis?.escalated_cases_count > 10 && (
                  <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg border border-red-200">
                    <span className="text-2xl font-black text-red-600">{kpis.escalated_cases_count}</span>
                    <p className="text-red-800 text-xs font-bold uppercase">Pending Escalations</p>
                  </div>
                )}
                {kpis?.avg_ai_confidence < 60 && (
                  <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg border border-red-200">
                    <span className="text-2xl font-black text-red-600">{kpis.avg_ai_confidence}%</span>
                    <p className="text-red-800 text-xs font-bold uppercase">Low AI Confidence</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
