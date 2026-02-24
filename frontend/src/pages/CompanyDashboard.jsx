import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Package, Tag, Phone, TrendingUp, Users, BarChart } from 'lucide-react';
import api from '@/api/api';
import { toast } from 'sonner';

export default function CompanyDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalBrands: 0,
    totalProducts: 0,
    activeBrands: 0,
    activeProducts: 0,
    totalCalls: 0,
    recentQueries: 0
  });

  useEffect(() => {
  }, []);

  const fetchDashboardStats = async () => {
    try {    fetchDashboardStats();

      setLoading(true);
      
      // Fetch brands
      const brandsResponse = await api.get('/company/brands');
      const brands = brandsResponse.data || [];
      
      // Fetch products
      const productsResponse = await api.get('/company/products');
      const products = productsResponse.data || [];
      
      setStats({
        totalBrands: brands.length,
        totalProducts: products.length,
        activeBrands: brands.filter(b => b.status === 'active').length,
        activeProducts: products.filter(p => p.status === 'active').length,
        totalCalls: 0, // Can be fetched from call analytics API
        recentQueries: 0
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
      title: 'Total Brands',
      value: stats.totalBrands,
      description: `${stats.activeBrands} active`,
      icon: Tag,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Total Products',
      value: stats.totalProducts,
      description: `${stats.activeProducts} active`,
      icon: Package,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: 'Total Calls',
      value: stats.totalCalls,
      description: 'All time',
      icon: Phone,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      title: 'Recent Queries',
      value: stats.recentQueries,
      description: 'Last 30 days',
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    }
  ];

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Company Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Welcome back, {user?.full_name || user?.username}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Tag className="h-5 w-5" />
              Brand Management
            </CardTitle>
            <CardDescription>
              Manage your company's brands
            </CardDescription>
          </CardHeader>
          <CardContent>
            <a 
              href="/company/brands" 
              className="text-sm text-primary hover:underline"
            >
              View all brands →
            </a>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Product Catalog
            </CardTitle>
            <CardDescription>
              Manage your product listings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <a 
              href="/company/products" 
              className="text-sm text-primary hover:underline"
            >
              View all products →
            </a>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart className="h-5 w-5" />
              Analytics
            </CardTitle>
            <CardDescription>
              View performance metrics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Coming soon...
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Company Info */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Company Information</CardTitle>
          <CardDescription>Your company details</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div>
              <span className="text-sm font-medium">Company:</span>
              <span className="text-sm text-muted-foreground ml-2">
                {user?.full_name || 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-sm font-medium">Email:</span>
              <span className="text-sm text-muted-foreground ml-2">
                {user?.email || 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-sm font-medium">Role:</span>
              <span className="text-sm text-muted-foreground ml-2 capitalize">
                {user?.role || 'N/A'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
