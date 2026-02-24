import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminAPI } from '@/api/api';
import DashboardStats from '@/components/DashboardStats';
import DocumentManagement from '@/components/DocumentManagement';
import { Loader2, Upload, Package } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetchStats();
    fetchUser();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await adminAPI.getDashboardStats();
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUser = () => {
    try {
      const userData = JSON.parse(localStorage.getItem('user') || '{}');
      setUser(userData);
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };

  const getCompanyId = () => {
    // Try to get company_id from user data or stats
    return user?.company_id || stats?.company_id || 1; // Default to 1 if not found
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen" data-testid="loading-spinner">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="dashboard-page">
      <div>
        <h2 className="text-4xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground mt-2 text-lg">Real-time overview of voice advisory system</p>
      </div>

      <DashboardStats stats={stats} />

      {/* Quick Actions */}
    

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DocumentManagement companyId={getCompanyId()} />
        
        <Card className="p-6 border border-border/60" data-testid="recent-activity-card">
          <h3 className="text-xl font-semibold mb-4">Recent Activity</h3>
          <p className="text-muted-foreground">Latest call sessions and advisories will appear here</p>
        </Card>

        <Card className="p-6 border border-border/60" data-testid="system-health-card">
          <h3 className="text-xl font-semibold mb-4">System Health</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm">Database</span>
              <span className="text-xs px-3 py-1 bg-green-100 text-green-800 border border-green-200 rounded-full">Connected</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Redis Cache</span>
              <span className="text-xs px-3 py-1 bg-green-100 text-green-800 border border-green-200 rounded-full">Active</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Vector DB</span>
              <span className="text-xs px-3 py-1 bg-green-100 text-green-800 border border-green-200 rounded-full">Connected</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}