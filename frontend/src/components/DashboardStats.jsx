import React from 'react';
import { Phone, Users, FileText, AlertCircle, Database, TrendingUp } from 'lucide-react';
import { Card } from '@/components/ui/card';

export default function DashboardStats({ stats }) {
  const statCards = [
    {
      title: 'Total Calls',
      value: stats?.total_calls || 0,
      icon: Phone,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      title: 'Active Calls',
      value: stats?.active_calls || 0,
      icon: Phone,
      color: 'text-accent',
      bgColor: 'bg-accent/10',
      pulse: stats?.active_calls > 0,
    },
    {
      title: 'Total Farmers',
      value: stats?.total_farmers || 0,
      icon: Users,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      title: 'Total Cases',
      value: stats?.total_cases || 0,
      icon: FileText,
      color: 'text-muted-foreground',
      bgColor: 'bg-muted',
    },
    {
      title: 'Pending Escalations',
      value: stats?.pending_escalations || 0,
      icon: AlertCircle,
      color: 'text-secondary',
      bgColor: 'bg-secondary/10',
    },
    {
      title: 'KB Entries',
      value: stats?.approved_kb_entries || 0,
      icon: Database,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
  ];

  return (
    <div data-testid="dashboard-stats" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {statCards.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <Card
            key={index}
            data-testid={`stat-card-${stat.title.toLowerCase().replace(/\s+/g, '-')}`}
            className={`p-6 border border-border/60 shadow-sm hover:border-primary/20 transition-all ${
              stat.pulse ? 'animate-pulse' : ''
            }`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground font-medium">{stat.title}</p>
                <p className="text-3xl font-bold mt-2 tabular-nums">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-full ${stat.bgColor}`}>
                <Icon className={`w-6 h-6 ${stat.color}`} strokeWidth={1.5} />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}