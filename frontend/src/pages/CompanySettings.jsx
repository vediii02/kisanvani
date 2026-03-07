// Company Settings Page
import React, { useState, useEffect } from 'react';
import { Settings, User, Lock, Bell, Shield, Building2, Mail, Phone } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { getErrorMessage } from '@/lib/utils';
import api from '@/api/api';

const CompanySettings = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('security');
  const [loading, setLoading] = useState(false);
  const [companyProfile, setCompanyProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  useEffect(() => {
    fetchCompanyProfile();
  }, []);

  const fetchCompanyProfile = async () => {
    try {
      setProfileLoading(true);
      const response = await api.get('/company/profile');
      setCompanyProfile(response.data);
    } catch (error) {
      console.error('Error fetching company profile:', error);
    } finally {
      setProfileLoading(false);
    }
  };

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
        old_password: passwordData.currentPassword,
        new_password: passwordData.newPassword
      });

      toast.success('Password updated successfully');
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'security', label: 'Security', icon: Lock },
    { id: 'company', label: 'Company Info', icon: Building2 },
  ];

  const companyInfoFields = [
    { label: 'Company Name', key: 'name', icon: Building2 },
    { label: 'Business Type', key: 'business_type', icon: Shield },
    { label: 'Brand Name', key: 'brand_name', icon: Shield },
    { label: 'Contact Person', key: 'contact_person', icon: User },
    { label: 'Phone', key: 'phone', icon: Phone },
    { label: 'Secondary Phone', key: 'secondary_phone', icon: Phone },
    { label: 'Email', key: 'email', icon: Mail },
    { label: 'Address', key: 'address' },
    { label: 'City', key: 'city' },
    { label: 'State', key: 'state' },
    { label: 'Pincode', key: 'pincode' },
    { label: 'Website', key: 'website_link' },
    { label: 'GST Number', key: 'gst_number' },
    { label: 'Registration Number', key: 'registration_number' },
    { label: 'Description', key: 'description' },
    { label: 'Notes', key: 'notes' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Settings className="h-8 w-8 text-primary" />
          Settings
        </h1>
        <p className="text-gray-600 mt-1">Manage your company account and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Settings Navigation */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader className="bg-slate-50 border-b border-slate-200">
              <CardTitle className="text-lg text-slate-800">Settings Menu</CardTitle>
            </CardHeader>
            <CardContent className="p-2">
              <nav className="space-y-1">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${activeTab === tab.id
                        ? 'bg-green-900 text-white shadow-md'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
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

                  <Button type="submit" disabled={loading} className="bg-green-800 hover:bg-green-900 text-white">
                    {loading ? 'Updating...' : 'Update Password'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}

          {activeTab === 'company' && (
            <div className="space-y-6">
              {profileLoading ? (
                <Card>
                  <CardContent className="flex items-center justify-center py-16">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-slate-900"></div>
                    <span className="ml-4 text-slate-500 text-lg">Loading company info...</span>
                  </CardContent>
                </Card>
              ) : companyProfile ? (
                <>
                  {/* Company Name Hero */}
                  <Card className="overflow-hidden border-slate-200">
                    <div className="bg-slate-50 px-8 py-8 border-b border-slate-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
                            <Building2 className="h-10 w-10 text-slate-600" />
                          </div>
                          <div>
                            <h2 className="text-2xl font-bold text-slate-900">
                              {companyProfile.name || 'Company Name'}
                            </h2>
                            <p className="text-slate-500 text-sm mt-1">Org: {companyProfile.organisation_name || 'N/A'}</p>
                          </div>
                        </div>
                        <span className={`px-4 py-2 text-sm font-bold rounded-full shadow-sm border ${companyProfile.status === 'active'
                          ? 'bg-green-50 text-green-700 border-green-200'
                          : 'bg-red-50 text-red-700 border-red-200'
                          }`}>
                          ● {(companyProfile.status || 'N/A').toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </Card>

                  {/* Business Details */}
                  <Card>
                    <CardHeader className="pb-3">
                      <div className="flex items-center gap-2">
                        <div className="p-2 bg-blue-50 rounded-lg">
                          <Shield className="h-5 w-5 text-blue-600" />
                        </div>
                        <CardTitle className="text-lg">Business Details</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="border-l-4 border-blue-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Organisation</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.organisation_name || '—'}</p>
                        </div>
                        <div className="border-l-4 border-blue-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Business Type</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.business_type || '—'}</p>
                        </div>
                        <div className="border-l-4 border-blue-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Brand Name</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.brand_name || '—'}</p>
                        </div>
                        <div className="border-l-4 border-blue-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Description</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.description || '—'}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Contact Information */}
                  <Card>
                    <CardHeader className="pb-3">
                      <div className="flex items-center gap-2">
                        <div className="p-2 bg-purple-50 rounded-lg">
                          <Phone className="h-5 w-5 text-purple-600" />
                        </div>
                        <CardTitle className="text-lg">Contact Information</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="border-l-4 border-purple-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Contact Person</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.contact_person || '—'}</p>
                        </div>
                        <div className="border-l-4 border-purple-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Email</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.email || '—'}</p>
                        </div>
                        <div className="border-l-4 border-purple-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Phone</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.phone || '—'}</p>
                        </div>
                        <div className="border-l-4 border-purple-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Secondary Phone</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.secondary_phone || '—'}</p>
                        </div>
                        {companyProfile.website_link && (
                          <div className="border-l-4 border-purple-400 pl-4 md:col-span-2">
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Website</p>
                            <p className="text-base font-medium text-blue-600 mt-1">{companyProfile.website_link}</p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Location */}
                  <Card>
                    <CardHeader className="pb-3">
                      <div className="flex items-center gap-2">
                        <div className="p-2 bg-orange-50 rounded-lg">
                          <Building2 className="h-5 w-5 text-orange-600" />
                        </div>
                        <CardTitle className="text-lg">Location</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="border-l-4 border-orange-400 pl-4 md:col-span-2">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Address</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.address || '—'}</p>
                        </div>
                        <div className="border-l-4 border-orange-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">City</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.city || '—'}</p>
                        </div>
                        <div className="border-l-4 border-orange-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">State</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.state || '—'}</p>
                        </div>
                        <div className="border-l-4 border-orange-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Pincode</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.pincode || '—'}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Legal & Compliance */}
                  <Card>
                    <CardHeader className="pb-3">
                      <div className="flex items-center gap-2">
                        <div className="p-2 bg-red-50 rounded-lg">
                          <Shield className="h-5 w-5 text-red-600" />
                        </div>
                        <CardTitle className="text-lg">Legal & Compliance</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="border-l-4 border-red-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">GST Number</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.gst_number || '—'}</p>
                        </div>
                        <div className="border-l-4 border-red-400 pl-4">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Registration Number</p>
                          <p className="text-base font-medium text-gray-800 mt-1">{companyProfile.registration_number || '—'}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Notes & Footer */}
                  {companyProfile.notes && (
                    <Card>
                      <CardContent className="pt-6">
                        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Notes</p>
                        <p className="text-sm text-gray-700 leading-relaxed">{companyProfile.notes}</p>
                      </CardContent>
                    </Card>
                  )}

                  {companyProfile.created_at && (
                    <div className="text-center text-sm text-gray-400 py-2">
                      Account created on {new Date(companyProfile.created_at).toLocaleDateString('en-IN', {
                        year: 'numeric', month: 'long', day: 'numeric'
                      })}
                    </div>
                  )}
                </>
              ) : (
                <Card>
                  <CardContent className="text-center py-16">
                    <Building2 className="h-16 w-16 text-gray-200 mx-auto mb-4" />
                    <p className="text-gray-500 text-lg">Company profile not available.</p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CompanySettings;
