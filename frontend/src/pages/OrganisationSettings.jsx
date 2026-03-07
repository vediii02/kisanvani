// Organisation Settings Page
import React, { useState, useEffect } from 'react';
import { Settings, User, Lock, Building2, Mail, Phone, Globe, Shield } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { getErrorMessage } from '@/lib/utils';
import api from '@/api/api';

const OrganisationSettings = () => {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('security');
    const [loading, setLoading] = useState(false);
    const [orgProfile, setOrgProfile] = useState(null);
    const [profileLoading, setProfileLoading] = useState(false);
    const [passwordData, setPasswordData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    });

    useEffect(() => {
        fetchOrganisationProfile();
    }, []);

    const fetchOrganisationProfile = async () => {
        try {
            setProfileLoading(true);
            const response = await api.get('/organisations/profile');
            setOrgProfile(response.data);
        } catch (error) {
            console.error('Error fetching organisation profile:', error);
            toast.error('Failed to load organisation information');
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

        if (passwordData.newPassword.length < 6) {
            toast.error('Password must be at least 6 characters long');
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
        { id: 'organisation', label: 'Organisation Info', icon: Building2 },
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <Settings className="h-8 w-8 text-primary" />
                    Organisation Settings
                </h1>
                <p className="text-gray-600 mt-1">Manage your organisation account and security preferences</p>
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
                                            minLength={6}
                                        />
                                        <p className="text-sm text-gray-500 mt-1">Minimum 6 characters</p>
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

                    {activeTab === 'organisation' && (
                        <div className="space-y-6">
                            {profileLoading ? (
                                <Card>
                                    <CardContent className="flex items-center justify-center py-16">
                                        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-500"></div>
                                        <span className="ml-4 text-gray-500 text-lg">Loading organisation info...</span>
                                    </CardContent>
                                </Card>
                            ) : orgProfile ? (
                                <>
                                    {/* Organisation Name Hero */}
                                    <Card className="overflow-hidden border-slate-200">
                                        <div className="bg-slate-50 px-8 py-8 border-b border-slate-200">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-4">
                                                    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
                                                        <Building2 className="h-10 w-10 text-slate-600" />
                                                    </div>
                                                    <div>
                                                        <h2 className="text-2xl font-bold text-slate-900">
                                                            {orgProfile.name || 'Organisation Name'}
                                                        </h2>
                                                        <p className="text-slate-500 text-sm mt-1">Plan: {orgProfile.plan_type?.toUpperCase() || 'BASIC'}</p>
                                                    </div>
                                                </div>
                                                <span className={`px-4 py-2 text-sm font-bold rounded-full shadow-sm border ${orgProfile.status === 'active'
                                                    ? 'bg-green-50 text-green-700 border-green-200'
                                                    : 'bg-red-50 text-red-700 border-red-200'
                                                    }`}>
                                                    ● {(orgProfile.status || 'N/A').toUpperCase()}
                                                </span>
                                            </div>
                                        </div>
                                    </Card>

                                    {/* General Details */}
                                    <Card>
                                        <CardHeader className="pb-3 border-b">
                                            <div className="flex items-center gap-2">
                                                <div className="p-2 bg-indigo-50 rounded-lg">
                                                    <Shield className="h-5 w-5 text-indigo-600" />
                                                </div>
                                                <CardTitle className="text-lg">Organisation Details</CardTitle>
                                            </div>
                                        </CardHeader>
                                        <CardContent className="pt-6">
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                <div className="space-y-1">
                                                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Email Address</p>
                                                    <div className="flex items-center gap-2 text-gray-800">
                                                        <Mail className="h-4 w-4 text-gray-400" />
                                                        <p className="font-medium">{orgProfile.email || '—'}</p>
                                                    </div>
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Contact Phone</p>
                                                    <div className="flex items-center gap-2 text-gray-800">
                                                        <Phone className="h-4 w-4 text-gray-400" />
                                                        <p className="font-medium">{orgProfile.phone_numbers || '—'}</p>
                                                    </div>
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Website</p>
                                                    <div className="flex items-center gap-2 text-gray-800">
                                                        <Globe className="h-4 w-4 text-gray-400" />
                                                        <p className="font-medium text-indigo-600">{orgProfile.website_link || '—'}</p>
                                                    </div>
                                                </div>
                                                <div className="space-y-1 md:col-span-2">
                                                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Description</p>
                                                    <p className="text-gray-700 bg-gray-50 p-3 rounded-lg border border-gray-100 italic">
                                                        {orgProfile.description || 'No description provided.'}
                                                    </p>
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>

                                    {/* Location Info */}
                                    <Card>
                                        <CardHeader className="pb-3 border-b">
                                            <div className="flex items-center gap-2">
                                                <div className="p-2 bg-purple-50 rounded-lg">
                                                    <Globe className="h-5 w-5 text-purple-600" />
                                                </div>
                                                <CardTitle className="text-lg">Location Information</CardTitle>
                                            </div>
                                        </CardHeader>
                                        <CardContent className="pt-6">
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                <div className="space-y-1 md:col-span-2">
                                                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Address</p>
                                                    <p className="text-gray-800 font-medium">{orgProfile.address || '—'}</p>
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">City</p>
                                                    <p className="text-gray-800 font-medium">{orgProfile.city || '—'}</p>
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">State & Pincode</p>
                                                    <p className="text-gray-800 font-medium">
                                                        {orgProfile.state}{orgProfile.pincode ? ` - ${orgProfile.pincode}` : ''}
                                                        {(!orgProfile.state && !orgProfile.pincode) ? '—' : ''}
                                                    </p>
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>

                                    {/* Footer Info */}
                                    <div className="text-center text-sm text-gray-400 py-4">
                                        Member since {new Date(orgProfile.created_at).toLocaleDateString('en-IN', {
                                            year: 'numeric', month: 'long', day: 'numeric'
                                        })}
                                    </div>
                                </>
                            ) : (
                                <Card>
                                    <CardContent className="text-center py-16">
                                        <Building2 className="h-16 w-16 text-gray-200 mx-auto mb-4" />
                                        <p className="text-gray-500 text-lg">Organisation information not available.</p>
                                    </CardContent>
                                </Card>
                            )}

                            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-4">
                                <Shield className="h-6 w-6 text-amber-600 shrink-0" />
                                <div>
                                    <h4 className="text-amber-800 font-bold">Profile Management</h4>
                                    <p className="text-amber-700 text-sm">
                                        To edit your organisation's public information, please head over to the
                                        <a href="/organisation/profile" className="mx-1 font-bold underline">Profile</a>
                                        page. This settings page is for security and account-level information.
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default OrganisationSettings;
