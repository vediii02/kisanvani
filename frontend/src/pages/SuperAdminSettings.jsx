import React, { useState } from 'react';
import { Settings, Lock } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { getErrorMessage } from '@/lib/utils';
import api from '@/api/api';

const SuperAdminSettings = () => {
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

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <Settings className="h-8 w-8 text-primary" />
                    Settings
                </h1>
                <p className="text-gray-600 mt-1">Manage your account security and preferences</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Lock className="h-5 w-5 text-green-800" />
                                <CardTitle>Security Settings</CardTitle>
                            </div>
                            <CardDescription>Update your password to keep your account secure</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handlePasswordChange} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="currentPassword">Current Password</Label>
                                    <Input
                                        id="currentPassword"
                                        type="password"
                                        placeholder="Enter current password"
                                        value={passwordData.currentPassword}
                                        onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                                        required
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="newPassword">New Password</Label>
                                    <Input
                                        id="newPassword"
                                        type="password"
                                        placeholder="Enter new password"
                                        value={passwordData.newPassword}
                                        onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                                        required
                                        minLength={8}
                                    />
                                    <p className="text-xs text-gray-500">Minimum 8 characters</p>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="confirmPassword">Confirm New Password</Label>
                                    <Input
                                        id="confirmPassword"
                                        type="password"
                                        placeholder="Confirm new password"
                                        value={passwordData.confirmPassword}
                                        onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                                        required
                                    />
                                </div>

                                <Button type="submit" disabled={loading} className="w-full md:w-auto bg-green-800 hover:bg-green-900 text-white">
                                    {loading ? 'Updating...' : 'Update Password'}
                                </Button>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default SuperAdminSettings;
