import React, { useEffect, useState } from 'react';
import { superAdminAPI } from '@/api/api';
import { Card } from '@/components/ui/card';
import { Loader2, Users, UserCog, UserCheck, UserX } from 'lucide-react';

export default function SuperAdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await superAdminAPI.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen" data-testid="loading-spinner">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Users',
      value: stats?.total_users || 0,
      icon: Users,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      title: 'Organisation Users',
      value: stats?.total_admins || 0,
      icon: UserCog,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Company Users',
      value: stats?.total_company_users || 0,
      icon: UserCog,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Active Users',
      value: stats?.active_users || 0,
      icon: UserCheck,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Inactive Users',
      value: stats?.inactive_users || 0,
      icon: UserX,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
  ];

  return (
    <div className="space-y-8" data-testid="superadmin-dashboard-page">
      <div>
        <h2 className="text-4xl font-bold tracking-tight">Super Admin Dashboard</h2>
        <p className="text-muted-foreground mt-2 text-lg">User management and system administration</p>
      </div>

      <div data-testid="superadmin-stats" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card
              key={index}
              data-testid={`stat-card-${stat.title.toLowerCase().replace(/\s+/g, '-')}`}
              className="p-6 border border-border/60 shadow-sm hover:border-primary/20 transition-all"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">{stat.title}</p>
                  <p className="text-3xl font-bold tracking-tight">{stat.value}</p>
                </div>
                <div className={`p-3 rounded-full ${stat.bgColor}`}>
                  <Icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
