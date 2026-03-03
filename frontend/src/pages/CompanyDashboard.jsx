import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Package, Tag, Phone, TrendingUp, Users, BarChart } from 'lucide-react';
import api from '@/api/api';
import { toast } from 'sonner';

export default function CompanyDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [companyProfile, setCompanyProfile] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [stats, setStats] = useState({
    totalBrands: 0,
    totalProducts: 0,
    activeBrands: 0,
    inactiveBrands: 0,
    activeProducts: 0,
    inactiveProducts: 0,
    totalCalls: 0,
    recentQueries: 0
  });

  useEffect(() => {
    fetchDashboardStats();
    fetchCompanyProfile();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setLoading(true);

      const [brandsRes, productsRes] = await Promise.all([
        api.get('/company/brands'),
        api.get('/company/products'),
      ]);

      const brands = brandsRes.data || [];
      const products = productsRes.data || [];

      setStats({
        totalBrands: brands.length,
        totalProducts: products.length,
        activeBrands: brands.filter(b => b.is_active).length,
        inactiveBrands: brands.filter(b => !b.is_active).length,
        activeProducts: products.filter(p => p.is_active).length,
        inactiveProducts: products.filter(p => !p.is_active).length,
        totalCalls: 0,
        recentQueries: 0
      });
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      toast.error('Failed to load dashboard statistics');
    }
  };

  const fetchCompanyProfile = async () => {
    try {
      const response = await api.get('/company/profile');
      setCompanyProfile(response.data);
      setEditForm(response.data);
    } catch (error) {
      console.error('Error fetching company profile:', error);
      toast.error('Failed to load company profile');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
    setEditForm(companyProfile);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditForm(companyProfile);
  };

  const handleInputChange = (field, value) => {
    setEditForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await api.put('/company/profile', editForm);
      setCompanyProfile(editForm);
      setIsEditing(false);
      toast.success('Company profile updated successfully');
    } catch (error) {
      console.error('Error updating company profile:', error);
      toast.error('Failed to update company profile');
    } finally {
      setSaving(false);
    }
  };

  const statCards = [
    {
      title: 'Total Brands',
      value: stats.totalBrands,
      active: stats.activeBrands,
      inactive: stats.inactiveBrands,
      icon: Tag,
      textColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
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
      active: 0,
      inactive: 0,
      icon: Phone,
      textColor: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
    },
    {
      title: 'Recent Queries',
      value: stats.recentQueries,
      active: 0,
      inactive: 0,
      icon: TrendingUp,
      textColor: 'text-amber-600',
      bgColor: 'bg-amber-50',
    }
  ];

  if (loading) {
    return (
      <div className="p-6 bg-white min-h-screen">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-slate-500 font-medium">Loading dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8 bg-white min-h-screen">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Company Dashboard</h1>
        <p className="text-slate-500 font-medium tracking-tight">
          Welcome back, {user?.full_name || user?.username}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-6">
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
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card
            className="cursor-pointer border border-slate-200 bg-white shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-200 group"
            onClick={() => navigate('/company/brands')}
          >
            <CardHeader>
              <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform duration-200">
                <Tag className="h-6 w-6" />
              </div>
              <CardTitle className="text-lg font-bold text-slate-900">Brand Management</CardTitle>
              <CardDescription className="text-slate-500 font-medium italic">Manage your company's brands</CardDescription>
            </CardHeader>
          </Card>

          <Card
            className="cursor-pointer border border-slate-200 bg-white shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-200 group"
            onClick={() => navigate('/company/products')}
          >
            <CardHeader>
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform duration-200">
                <Package className="h-6 w-6" />
              </div>
              <CardTitle className="text-lg font-bold text-slate-900">Product Catalog</CardTitle>
              <CardDescription className="text-slate-500 font-medium italic">Manage your product listings</CardDescription>
            </CardHeader>
          </Card>

          <Card className="border border-slate-200 bg-slate-50/50 shadow-sm opacity-80">
            <CardHeader>
              <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-400 flex items-center justify-center mb-2">
                <BarChart className="h-6 w-6" />
              </div>
              <CardTitle className="text-lg font-bold text-slate-400">Analytics</CardTitle>
              <CardDescription className="text-slate-400 font-medium italic italic">Coming soon</CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    </div>
  );
}
