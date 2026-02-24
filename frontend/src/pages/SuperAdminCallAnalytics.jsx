import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Loader2, Phone, Clock, TrendingUp, TrendingDown, Users, CheckCircle, XCircle, BarChart3 } from 'lucide-react';
import api from '../api/api';

export default function SuperAdminCallAnalytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('today'); // today, week, month

  useEffect(() => {
    fetchAnalytics();
  }, [dateRange]);

  const fetchAnalytics = async () => {
    try {
      const response = await api.get(`/superadmin-platform/call-analytics?range=${dateRange}`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Calls',
      value: analytics?.total_calls || 0,
      icon: Phone,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      trend: '+12%'
    },
    {
      title: 'Avg Duration',
      value: `${Math.round((analytics?.avg_duration_seconds || 0) / 60)}m`,
      icon: Clock,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      trend: '+5%'
    },
    {
      title: 'AI Resolution Rate',
      value: `${Math.round(analytics?.ai_resolution_rate || 0)}%`,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      trend: '+8%'
    },
    {
      title: 'Human Resolution Rate',
      value: `${Math.round(analytics?.human_resolution_rate || 0)}%`,
      icon: Users,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      trend: '-3%'
    }
  ];

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Call Analytics</h2>
          <p className="text-muted-foreground mt-2">Platform-wide call metrics and insights</p>
        </div>
        <select
          value={dateRange}
          onChange={(e) => setDateRange(e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="today">Today</option>
          <option value="week">This Week</option>
          <option value="month">This Month</option>
          <option value="all">All Time</option>
        </select>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <Card key={index} className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">{stat.title}</p>
                <p className="text-3xl font-bold">{stat.value}</p>
                <p className={`text-sm mt-2 ${stat.trend.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
                  {stat.trend} from last period
                </p>
              </div>
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Top Crops */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Top Crops by Call Volume
        </h3>
        <div className="space-y-4">
          {analytics?.top_crops?.slice(0, 5).map((crop, index) => (
            <div key={index} className="flex items-center gap-4">
              <div className="w-24 text-sm font-medium">{crop.crop}</div>
              <div className="flex-1 bg-gray-200 rounded-full h-6 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-green-400 to-green-600 h-full flex items-center justify-end pr-2"
                  style={{ width: `${(crop.count / analytics.total_calls) * 100}%` }}
                >
                  <span className="text-xs text-white font-bold">{crop.count}</span>
                </div>
              </div>
              <div className="w-16 text-sm text-gray-600 text-right">
                {Math.round((crop.count / analytics.total_calls) * 100)}%
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Top Problems */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <XCircle className="h-5 w-5 text-red-600" />
          Top Problems Reported
        </h3>
        <div className="space-y-4">
          {analytics?.top_problems?.slice(0, 5).map((problem, index) => (
            <div key={index} className="flex items-center gap-4">
              <div className="w-32 text-sm font-medium truncate">{problem.problem}</div>
              <div className="flex-1 bg-gray-200 rounded-full h-6 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-red-400 to-red-600 h-full flex items-center justify-end pr-2"
                  style={{ width: `${(problem.count / analytics.total_calls) * 100}%` }}
                >
                  <span className="text-xs text-white font-bold">{problem.count}</span>
                </div>
              </div>
              <div className="w-16 text-sm text-gray-600 text-right">
                {Math.round((problem.count / analytics.total_calls) * 100)}%
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Calls by Hour */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4">Calls by Hour of Day</h3>
        <div className="grid grid-cols-12 gap-2">
          {analytics?.calls_by_hour?.map((hour, index) => (
            <div key={index} className="flex flex-col items-center">
              <div className="text-xs text-gray-500 mb-1">{hour.hour}h</div>
              <div
                className="w-full bg-gradient-to-t from-blue-500 to-blue-300 rounded-t"
                style={{ height: `${(hour.count / Math.max(...analytics.calls_by_hour.map(h => h.count))) * 100}px` }}
                title={`${hour.count} calls`}
              ></div>
              <div className="text-xs font-medium mt-1">{hour.count}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Organisation-wise Distribution */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4">Organisation-wise Call Distribution</h3>
        <div className="space-y-3">
          {analytics?.org_distribution?.map((org, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium">{org.organisation_name}</p>
                <p className="text-sm text-gray-600">{org.call_count} calls</p>
              </div>
              <div className="text-right">
                <p className="font-bold text-lg">{Math.round((org.call_count / analytics.total_calls) * 100)}%</p>
                <p className="text-xs text-gray-500">of total</p>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
