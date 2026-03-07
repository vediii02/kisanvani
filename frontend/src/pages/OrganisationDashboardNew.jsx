// Organisation Dashboard
import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, Tag, Package, Users, TrendingUp, BarChart, Phone, LayoutDashboard } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import api from '@/api/api';
import { toast } from 'sonner';

export default function OrganisationDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalCompanies: 0,
    totalBrands: 0,
    totalProducts: 0,
    activeCompanies: 0,
    inactiveCompanies: 0,
    activeBrands: 0,
    inactiveBrands: 0,
    activeProducts: 0,
    inactiveProducts: 0,
    totalCalls: 0,
  });

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setLoading(true);

      const response = await api.get('/organisation/companies/stats/summary');
      if (response.data) {
        setStats(response.data);
      }
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      toast.error('Failed to load dashboard statistics');
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Total Companies',
      value: stats.totalCompanies,
      active: stats.activeCompanies,
      inactive: stats.inactiveCompanies,
      icon: Building2,
      textColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Total Brands',
      value: stats.totalBrands,
      active: stats.activeBrands,
      inactive: stats.inactiveBrands,
      icon: Tag,
      textColor: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
    },
    {
      title: 'Total Products',
      value: stats.totalProducts,
      active: stats.activeProducts,
      inactive: stats.inactiveProducts,
      icon: Package,
      textColor: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
    },
    {
      title: 'Total Calls',
      value: stats.totalCalls,
      active: stats.totalCalls,
      inactive: 0,
      icon: Phone,
      textColor: 'text-amber-600',
      bgColor: 'bg-amber-50',
    },
  ];

  const quickActions = [
    {
      title: 'Manage Companies',
      description: 'View and manage your companies',
      icon: Building2,
      textColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
      path: '/organisation/companies',
    },
    {
      title: 'Manage Brands',
      description: 'View and edit your brands',
      icon: Tag,
      textColor: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      path: '/organisation/brands',
    },
    {
      title: 'Manage Products',
      description: 'View and update products',
      icon: Package,
      textColor: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      path: '/organisation/products',
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 p-6 bg-white min-h-screen">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <LayoutDashboard className="w-8 h-8 text-primary" />
          Organisation Dashboard
        </h1>
        <p className="text-slate-500 font-medium tracking-tight">Welcome back, {user?.username}!</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index} className="relative overflow-hidden border border-slate-200 bg-white shadow-sm hover:shadow-md transition-all duration-200">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-2.5 rounded-xl ${stat.bgColor} ${stat.textColor}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{stat.title}</span>
                </div>

                <div className="flex items-baseline gap-2">
                  <div className="text-4xl font-bold text-slate-900">{stat.value}</div>
                </div>

                <div className="flex items-center gap-3 mt-6">
                  <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-50 text-slate-600 rounded-lg border border-slate-100 text-xs font-semibold">
                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
                    {stat.active} Active
                  </div>
                  <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-50 text-slate-600 rounded-lg border border-slate-100 text-xs font-semibold">
                    <span className="w-1.5 h-1.5 bg-slate-300 rounded-full"></span>
                    {stat.inactive} Inactive
                  </div>
                </div>
              </div>
              <div className={`absolute bottom-0 left-0 right-0 h-1 ${stat.bgColor.replace('bg-', 'bg-').replace('-50', '-200')}`} />
            </Card>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action, index) => {
            const Icon = action.icon;
            return (
              <Card
                key={index}
                className="cursor-pointer border border-slate-200 bg-white shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-200 group"
                onClick={() => navigate(action.path)}
              >
                <CardHeader>
                  <div className={`w-12 h-12 rounded-xl ${action.bgColor} ${action.textColor} flex items-center justify-center mb-2 group-hover:scale-110 transition-transform duration-200`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <CardTitle className="text-lg font-bold text-slate-900">{action.title}</CardTitle>
                  <CardDescription className="text-slate-500 font-medium italic">{action.description}</CardDescription>
                </CardHeader>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Organisation Info */}
      {/* <Card>
        <CardHeader>
          <CardTitle>Organisation Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Organisation Name</p>
              <p className="font-medium mt-1">{user?.organisation_name || 'Not Available'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">User Role</p>
              <p className="font-medium mt-1 capitalize">{user?.role || 'organisation'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Email</p>
              <p className="font-medium mt-1">{user?.email || 'Not Available'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <span className="inline-block px-3 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium mt-1">
                Active
              </span>
            </div>
          </div>
        </CardContent>
      </Card> */}

      {/* Recent Activity */}
      {/* <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest updates across your organisation</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <BarChart className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>Activity tracking coming soon</p>
          </div>
        </CardContent>
      </Card> */}
    </div>
  );
}
