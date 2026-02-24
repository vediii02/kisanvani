// Company Settings Page
import React, { useState } from 'react';
import { Settings, User, Lock, Bell, Shield, Building2, Mail, Phone } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import api from '@/api/api';

const CompanySettings = () => {
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
    { id: 'company', label: 'Company Info', icon: Building2 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl shadow-lg">
          <Settings className="h-8 w-8 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">Manage your company account and preferences</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Settings Navigation */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader className="bg-gradient-to-r from-green-500 to-emerald-600 text-white">
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
                          ? 'bg-green-50 text-green-600 font-medium'
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
              </CardContent>
            </Card>
          )}

          {activeTab === 'profile' && (
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>View and update your profile details</CardDescription>
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
                  <Input value={user?.role || ''} disabled className="capitalize" />
                </div>
                <p className="text-sm text-gray-500">
                  Contact your organisation administrator to update profile information.
                </p>
              </CardContent>
            </Card>
          )}

          {activeTab === 'notifications' && (
            <Card>
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>Manage how you receive notifications</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Email Notifications</p>
                      <p className="text-sm text-gray-500">Receive updates via email</p>
                    </div>
                    <input type="checkbox" className="toggle" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Product Alerts</p>
                      <p className="text-sm text-gray-500">Notifications about your products</p>
                    </div>
                    <input type="checkbox" className="toggle" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Brand Updates</p>
                      <p className="text-sm text-gray-500">Updates about your brands</p>
                    </div>
                    <input type="checkbox" className="toggle" defaultChecked />
                  </div>
                  <p className="text-sm text-gray-500 mt-4">
                    Notification settings will be saved automatically.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'company' && (
            <Card>
              <CardHeader>
                <CardTitle>Company Information</CardTitle>
                <CardDescription>Your company details and settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Company Name</Label>
                    <div className="flex items-center gap-2 mt-2">
                      <Building2 className="h-4 w-4 text-gray-500" />
                      <span className="text-sm">{user?.company_name || 'Not Available'}</span>
                    </div>
                  </div>
                  <div>
                    <Label>Status</Label>
                    <div className="mt-2">
                      <span className="px-3 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        Active
                      </span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <Label>Organisation</Label>
                  <div className="flex items-center gap-2 mt-2">
                    <Shield className="h-4 w-4 text-gray-500" />
                    <span className="text-sm">{user?.organisation_name || 'Not Available'}</span>
                  </div>
                </div>
                
                <div className="pt-4 border-t">
                  <p className="text-sm text-gray-500">
                    For changes to company information, please contact your organisation administrator.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default CompanySettings;
