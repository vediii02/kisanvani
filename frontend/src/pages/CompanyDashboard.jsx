import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Package, Tag, Phone, TrendingUp, Users, BarChart, LayoutDashboard, PhoneCall, Info } from 'lucide-react';
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
      const response = await api.get('/company/stats');
      setStats(response.data);
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
        <h1 className="text-3xl font-bold flex items-center gap-2 text-slate-900 tracking-tight">
          <LayoutDashboard className="w-8 h-8 text-primary" />
          Company Dashboard
        </h1>
        <p className="text-slate-500 font-medium tracking-tight">
          Welcome back, {user?.username}!
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

      {/* Call Forwarding Setup Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6 relative overflow-hidden group mb-2">
        <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:scale-110 transition-transform duration-500">
          <PhoneCall className="h-24 w-24 text-blue-400" />
        </div>
        <div className="flex items-start gap-4 relative z-10">
          <div className="p-2 bg-blue-100 rounded-lg shrink-0">
            <Info className="h-6 w-6 text-blue-600" />
          </div>
          <div className="w-full">
            <h4 className="font-bold text-gray-800 text-lg tracking-tight mb-2">Important: Call Forwarding Setup</h4>
            <p className="text-gray-500 text-sm font-medium mb-6 max-w-3xl leading-relaxed">
              To begin receiving advisory calls, companies must set their phones to forward incoming calls to their assigned Virtual Number. Use these standard USSD codes to manage call forwarding.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Step 1: Turn OFF */}
              <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex flex-col h-full">
                <div className="flex items-center gap-2 mb-3">
                  <span className="h-6 w-6 rounded-full bg-gray-100 text-gray-700 flex items-center justify-center text-xs font-bold shrink-0">1</span>
                  <h5 className="font-bold text-gray-800">To Turn OFF Call Forwarding (Deactivate)</h5>
                </div>
                <p className="text-gray-500 text-xs mb-auto">When you are done testing and want the company phone to ring normally again, pick up the company's mobile phone and dial:</p>
                <div className="mt-4 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200 text-center">
                  <code className="text-lg text-gray-800 font-mono font-bold tracking-widest">##21#</code>
                </div>
              </div>

              {/* Step 2: Turn ON */}
              <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm shadow-gray-50/50 flex flex-col h-full ring-1 ring-gray-50">
                <div className="flex items-center gap-2 mb-3">
                  <span className="h-6 w-6 rounded-full bg-gray-100 text-gray-700 flex items-center justify-center text-xs font-bold shrink-0">2</span>
                  <h5 className="font-bold text-gray-800">To Turn ON Call Forwarding (Activate for Testing)</h5>
                </div>
                <p className="text-gray-500 text-xs mb-auto">When you are ready to test the AI voice agent, pick up the company's mobile phone and dial:</p>
                <div className="mt-4 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200 text-center flex flex-col items-center">
                  <code className="text-lg text-gray-800 font-mono font-bold whitespace-nowrap">
                    **21*02249360001#
                  </code>
                </div>
              </div>

              {/* Step 3: Check Status */}
              <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex flex-col h-full">
                <div className="flex items-center gap-2 mb-3">
                  <span className="h-6 w-6 rounded-full bg-gray-100 text-gray-700 flex items-center justify-center text-xs font-bold shrink-0">3</span>
                  <h5 className="font-bold text-gray-800">To CHECK the Status</h5>
                </div>
                <p className="text-gray-500 text-xs mb-auto">If you ever forget whether the forwarding is currently active or not to your virtual number, dial:</p>
                <div className="mt-4 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200 text-center">
                  <code className="text-lg text-gray-800 font-mono font-bold tracking-widest">*#21#</code>
                </div>
              </div>
            </div>
          </div>
        </div>
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
