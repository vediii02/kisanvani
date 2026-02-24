import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { User, Mail, Shield, Calendar, Key } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';
import api from '@/api/api';

export default function Profile() {
  const { user } = useAuth();
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [editData, setEditData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
  });
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });

  const handleUpdateProfile = async () => {
    try {
      await api.put('/auth/profile', editData);
      toast.success('Profile updated successfully');
      setEditDialogOpen(false);
      window.location.reload();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    }
  };

  const handleChangePassword = async () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    try {
      await api.post('/auth/change-password', {
        old_password: passwordData.old_password,
        new_password: passwordData.new_password,
      });
      toast.success('Password changed successfully');
      setPasswordDialogOpen(false);
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to change password');
    }
  };

  return (
    <div className="space-y-6" data-testid="profile-page">
      <div>
        <h2 className="text-4xl font-bold tracking-tight">Profile</h2>
        <p className="text-muted-foreground mt-2 text-lg">Manage your account settings</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 border border-border/60" data-testid="profile-info-card">
          <h3 className="text-xl font-semibold mb-6">Personal Information</h3>

          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Full Name</p>
                <p className="font-medium" data-testid="profile-fullname">{user?.full_name}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Username</p>
                <p className="font-medium" data-testid="profile-username">{user?.username}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                <Mail className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Email</p>
                <p className="font-medium" data-testid="profile-email">{user?.email}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                <Shield className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Role</p>
                <p className="font-medium capitalize" data-testid="profile-role">{user?.role}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                <Calendar className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Member Since</p>
                <p className="font-medium" data-testid="profile-created">
                  {user?.created_at ? format(new Date(user.created_at), 'MMM dd, yyyy') : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-border">
            <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
              <DialogTrigger asChild>
                <Button className="w-full rounded-full" data-testid="edit-profile-btn">
                  Edit Profile
                </Button>
              </DialogTrigger>
              <DialogContent data-testid="edit-profile-dialog">
                <DialogHeader>
                  <DialogTitle>Edit Profile</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="edit-fullname">Full Name</Label>
                    <Input
                      id="edit-fullname"
                      value={editData.full_name}
                      onChange={(e) => setEditData({ ...editData, full_name: e.target.value })}
                      data-testid="edit-fullname-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="edit-email">Email</Label>
                    <Input
                      id="edit-email"
                      type="email"
                      value={editData.email}
                      onChange={(e) => setEditData({ ...editData, email: e.target.value })}
                      data-testid="edit-email-input"
                    />
                  </div>
                  <Button onClick={handleUpdateProfile} className="w-full rounded-full" data-testid="save-profile-btn">
                    Save Changes
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </Card>

        <Card className="p-6 border border-border/60" data-testid="security-card">
          <h3 className="text-xl font-semibold mb-6">Security</h3>

          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                <Key className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Password</p>
                <p className="font-medium">••••••••</p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-border">
            <Dialog open={passwordDialogOpen} onOpenChange={setPasswordDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="w-full rounded-full" data-testid="change-password-btn">
                  Change Password
                </Button>
              </DialogTrigger>
              <DialogContent data-testid="change-password-dialog">
                <DialogHeader>
                  <DialogTitle>Change Password</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="old-password">Old Password</Label>
                    <Input
                      id="old-password"
                      type="password"
                      value={passwordData.old_password}
                      onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
                      data-testid="old-password-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="new-password">New Password</Label>
                    <Input
                      id="new-password"
                      type="password"
                      value={passwordData.new_password}
                      onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                      data-testid="new-password-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="confirm-password">Confirm New Password</Label>
                    <Input
                      id="confirm-password"
                      type="password"
                      value={passwordData.confirm_password}
                      onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                      data-testid="confirm-password-input"
                    />
                  </div>
                  <Button onClick={handleChangePassword} className="w-full rounded-full" data-testid="save-password-btn">
                    Update Password
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </Card>
      </div>
    </div>
  );
}