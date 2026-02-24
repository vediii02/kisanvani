// Admin Settings Page
import React, { useState } from 'react';
import { Settings, User, Lock, Bell, Shield, Globe, Database } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import api from '@/api/api';

const AdminSettings = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('security');
  const [loading, setLoading] = useState(false);
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    if (passwordData.newPassword.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return;
    }

    try {
      setLoading(true);
      await api.post('/auth/change-password', {
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword
      });
      
      toast.success('Password updated successfully');
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update password');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'security', label: 'Security', icon: Lock },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'system', label: 'System', icon: Database },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl shadow-lg">
          <Settings className="h-8 w-8 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Settings</h1>
          <p className="text-gray-600 mt-1">Manage your admin account and system preferences</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Settings Navigation */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader className="bg-gradient-to-r from-purple-500 to-pink-600 text-white">
              <CardTitle className="text-lg">Settings Menu</CardTitle>
            </CardHeader>
            <CardContent className="p-2">
              <nav className="space-y-1">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all ${
                        activeTab === tab.id
                          ? 'bg-purple-50 text-purple-600 font-medium'
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                      {tab.label}
                    </button>
                  );
                })}
              </nav>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          {activeTab === 'security' && (
            <Card>
              <CardHeader>
                <CardTitle>Security Settings</CardTitle>
                <CardDescription>Update your password and security preferences</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePasswordChange} className="space-y-4">
                  <div>
                    <Label htmlFor="currentPassword">Current Password</Label>
                    <Input
                      id="currentPassword"
                      type="password"
                      value={passwordData.currentPassword}
                      onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="newPassword">New Password</Label>
                    <Input
                      id="newPassword"
                      type="password"
                      value={passwordData.newPassword}
                      onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                      required
                      minLength={8}
                    />
                    <p className="text-sm text-gray-500 mt-1">Minimum 8 characters</p>
                  </div>
                  
                  <div>
                    <Label htmlFor="confirmPassword">Confirm New Password</Label>
                    <Input
                      id="confirmPassword"
                      type="password"
                      value={passwordData.confirmPassword}
                      onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                      required
                    />
                  </div>
                  
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Updating...' : 'Update Password'}
                  </Button>
                </form>

                <div className="mt-6 pt-6 border-t">
                  <h4 className="font-medium mb-2">Two-Factor Authentication</h4>
                  <p className="text-sm text-gray-500 mb-3">
                    Add an extra layer of security to your account
                  </p>
                  <Button variant="outline" disabled>
                    Enable 2FA (Coming Soon)
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'profile' && (
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>View and update your admin profile</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Username</Label>
                  <Input value={user?.username || ''} disabled />
                </div>
                <div>
                  <Label>Email</Label>
                  <Input value={user?.email || ''} disabled />
                </div>
                <div>
                  <Label>Role</Label>
                  <div className="mt-2">
                    <span className="px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full font-medium">
                      {user?.role || 'Admin'}
                    </span>
                  </div>
                </div>
                <div className="pt-4 border-t">
                  <Label>Admin Privileges</Label>
                  <ul className="mt-2 space-y-2 text-sm text-gray-600">
                    <li className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-green-600" />
                      Full system access
                    </li>
                    <li className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-green-600" />
                      User management
                    </li>
                    <li className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-green-600" />
                      Organisation management
                    </li>
                    <li className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-green-600" />
                      System configuration
                    </li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'notifications' && (
            <Card>
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>Manage how you receive system notifications</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Email Notifications</p>
                      <p className="text-sm text-gray-500">Receive system updates via email</p>
                    </div>
                    <input type="checkbox" className="toggle" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">System Alerts</p>
                      <p className="text-sm text-gray-500">Critical system notifications</p>
                    </div>
                    <input type="checkbox" className="toggle" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">User Activity</p>
                      <p className="text-sm text-gray-500">Notifications about user actions</p>
                    </div>
                    <input type="checkbox" className="toggle" />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Security Alerts</p>
                      <p className="text-sm text-gray-500">Security-related notifications</p>
                    </div>
                    <input type="checkbox" className="toggle" defaultChecked />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'system' && (
            <Card>
              <CardHeader>
                <CardTitle>System Information</CardTitle>
                <CardDescription>Platform status and configuration</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Platform Version</Label>
                    <p className="text-sm mt-1">v1.0.0</p>
                  </div>
                  <div>
                    <Label>Environment</Label>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                      Production
                    </span>
                  </div>
                </div>

                <div>
                  <Label>System Status</Label>
                  <div className="grid grid-cols-2 gap-3 mt-2">
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <span className="text-sm">Database</span>
                      <span className="text-xs text-green-600 font-medium">Connected</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <span className="text-sm">API</span>
                      <span className="text-xs text-green-600 font-medium">Active</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <span className="text-sm">Redis</span>
                      <span className="text-xs text-green-600 font-medium">Connected</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <span className="text-sm">Vector DB</span>
                      <span className="text-xs text-green-600 font-medium">Active</span>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <Label>Database Statistics</Label>
                  <div className="grid grid-cols-3 gap-3 mt-2 text-sm">
                    <div>
                      <p className="text-gray-500">Total Users</p>
                      <p className="text-xl font-bold">6</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Organisations</p>
                      <p className="text-xl font-bold">3</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Companies</p>
                      <p className="text-xl font-bold">3</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminSettings;
