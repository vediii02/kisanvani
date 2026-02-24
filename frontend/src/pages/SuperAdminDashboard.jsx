import React, { useEffect, useState } from 'react';
import { superAdminAPI } from '@/api/api';
import { Card } from '@/components/ui/card';
import { Loader2, Users, Shield, UserCog, UserCheck, UserX, Phone, Database, Cpu, MessageSquare } from 'lucide-react';

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
      title: 'Admins',
      value: stats?.total_admins || 0,
      icon: Shield,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Operators',
      value: stats?.total_operators || 0,
      icon: UserCog,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Supervisors',
      value: stats?.total_supervisors || 0,
      icon: UserCog,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
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

  const newFeatureCards = [
    {
      title: 'Call Flow System',
      description: '7-state call management with AI',
      icon: Phone,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100',
      status: '✅ Active',
      details: 'INCOMING → GREETING → PROFILING → ADVISORY → CLOSURE'
    },
    {
      title: 'RAG Pipeline',
      description: 'Vector-based knowledge retrieval',
      icon: Database,
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-100',
      status: '⚙️ Backend Ready',
      details: 'Qdrant + GPT-4o + Confidence Scoring'
    },
    {
      title: 'State Machine',
      description: 'Smart call routing & transitions',
      icon: Cpu,
      color: 'text-violet-600',
      bgColor: 'bg-violet-100',
      status: '✅ Implemented',
      details: '8 new tables + APIs ready'
    },
    {
      title: 'Farmer Profiling',
      description: '11 questions one-by-one in Hindi',
      icon: MessageSquare,
      color: 'text-amber-600',
      bgColor: 'bg-amber-100',
      status: '🔨 In Progress',
      details: 'NLU-based answer extraction'
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

      {/* New Features Section */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-4">
          {/* <h2 className="text-2xl font-bold text-foreground">🚀 New Features (Just Added)</h2> */}
          {/* <span className="text-sm px-3 py-1 bg-green-100 text-green-700 rounded-full font-medium">
            Backend Ready
          </span> */}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {newFeatureCards.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card key={index} className="p-6 hover:shadow-xl transition-all border-2 hover:border-primary/50">
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-lg ${feature.bgColor} shrink-0`}>
                    <Icon className={`w-6 h-6 ${feature.color}`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-semibold text-foreground">{feature.title}</h3>
                      <span className="text-xs px-2 py-1 bg-gray-100 rounded-full">
                        {feature.status}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">{feature.description}</p>
                    <p className="text-xs text-gray-500 font-mono bg-gray-50 p-2 rounded">
                      {feature.details}
                    </p>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Technical Details */}
      <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
        <h3 className="text-lg font-semibold mb-3 text-blue-900">📊 Technical Infrastructure</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="bg-white p-3 rounded-lg shadow-sm">
            <p className="text-gray-500 text-xs mb-1">Database Tables</p>
            <p className="text-2xl font-bold text-blue-600">24</p>
            <p className="text-xs text-green-600 mt-1">+8 new</p>
          </div>
          <div className="bg-white p-3 rounded-lg shadow-sm">
            <p className="text-gray-500 text-xs mb-1">API Endpoints</p>
            <p className="text-2xl font-bold text-purple-600">45+</p>
            <p className="text-xs text-green-600 mt-1">+12 new</p>
          </div>
          <div className="bg-white p-3 rounded-lg shadow-sm">
            <p className="text-gray-500 text-xs mb-1">Call States</p>
            <p className="text-2xl font-bold text-emerald-600">7</p>
            <p className="text-xs text-gray-500 mt-1">State machine</p>
          </div>
          <div className="bg-white p-3 rounded-lg shadow-sm">
            <p className="text-gray-500 text-xs mb-1">Vector DB</p>
            <p className="text-2xl font-bold text-cyan-600">Qdrant</p>
            <p className="text-xs text-gray-500 mt-1">For RAG</p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 border border-border/60" data-testid="quick-actions-card">
          <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <div className="text-sm text-muted-foreground">
              • View and manage all users
            </div>
            <div className="text-sm text-muted-foreground">
              • Create new admin accounts
            </div>
            <div className="text-sm text-muted-foreground">
              • Reset user passwords
            </div>
            <div className="text-sm text-muted-foreground">
              • Activate/deactivate user accounts
            </div>
          </div>
        </Card>

        <Card className="p-6 border border-border/60" data-testid="system-info-card">
          <h3 className="text-xl font-semibold mb-4">System Information</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm">Platform Version</span>
              <span className="text-xs px-3 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full">
                v1.0.0
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Database</span>
              <span className="text-xs px-3 py-1 bg-green-100 text-green-800 border border-green-200 rounded-full">
                MySQL Connected
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Authentication</span>
              <span className="text-xs px-3 py-1 bg-green-100 text-green-800 border border-green-200 rounded-full">
                JWT Active
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
