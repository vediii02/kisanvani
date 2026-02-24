// Organisation Dashboard
import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, Tag, Package, Users, TrendingUp, BarChart, Phone } from 'lucide-react';
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
    activeBrands: 0,
    activeProducts: 0,
    totalCalls: 0,
  });

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setLoading(true);
      
      // Fetch companies
      const companiesResponse = await api.get('/organisation/companies');
      const companies = companiesResponse.data || [];
      
      // Fetch brands
      const brandsResponse = await api.get('/organisation/brands');
      const brands = brandsResponse.data || [];
      
      // Fetch products
      const productsResponse = await api.get('/organisation/products');
      const products = productsResponse.data || [];
      
      setStats({
        totalCompanies: companies.length,
        totalBrands: brands.length,
        totalProducts: products.length,
        activeCompanies: companies.filter(c => c.status === 'active').length,
        activeBrands: brands.filter(b => b.status === 'active').length,
        activeProducts: products.filter(p => p.status === 'active').length,
        totalCalls: 0, // Can be fetched from call analytics API
      });
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
      subtitle: `${stats.activeCompanies} active`,
      icon: Building2,
      color: 'from-blue-500 to-cyan-500',
      bgColor: 'bg-blue-50',
      iconColor: 'text-blue-600',
    },
    {
      title: 'Total Brands',
      value: stats.totalBrands,
      subtitle: `${stats.activeBrands} active`,
      icon: Tag,
      color: 'from-purple-500 to-pink-500',
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-600',
    },
    {
      title: 'Total Products',
      value: stats.totalProducts,
      subtitle: `${stats.activeProducts} active`,
      icon: Package,
      color: 'from-green-500 to-emerald-500',
      bgColor: 'bg-green-50',
      iconColor: 'text-green-600',
    },
    {
      title: 'Total Calls',
      value: stats.totalCalls,
      subtitle: 'This month',
      icon: Phone,
      color: 'from-orange-500 to-red-500',
      bgColor: 'bg-orange-50',
      iconColor: 'text-orange-600',
    },
  ];

  const quickActions = [
    {
      title: 'Manage Companies',
      description: 'View and manage your companies',
      icon: Building2,
      color: 'from-blue-500 to-cyan-500',
      path: '/organisation/companies',
    },
    {
      title: 'Manage Brands',
      description: 'View and edit your brands',
      icon: Tag,
      color: 'from-purple-500 to-pink-500',
      path: '/organisation/brands',
    },
    {
      title: 'Manage Products',
      description: 'View and update products',
      icon: Package,
      color: 'from-green-500 to-emerald-500',
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
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Organisation Dashboard</h1>
        <p className="text-gray-600 mt-2">Welcome back, {user?.username}!</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index} className="overflow-hidden">
              <CardHeader className={`bg-gradient-to-r ${stat.color} text-white pb-2`}>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                  <Icon className="h-5 w-5 opacity-80" />
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="text-3xl font-bold text-gray-900">{stat.value}</div>
                <p className="text-sm text-gray-600 mt-1">{stat.subtitle}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action, index) => {
            const Icon = action.icon;
            return (
              <Card 
                key={index} 
                className="cursor-pointer hover:shadow-lg transition-shadow"
                onClick={() => navigate(action.path)}
              >
                <CardHeader>
                  <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${action.color} flex items-center justify-center mb-3`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-lg">{action.title}</CardTitle>
                  <CardDescription>{action.description}</CardDescription>
                </CardHeader>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Organisation Info */}
      <Card>
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
      </Card>

      {/* Recent Activity */}
      <Card>
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
      </Card>
    </div>
  );
}
