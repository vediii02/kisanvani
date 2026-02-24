import React, { useEffect, useState } from 'react';
import { superAdminAPI } from '@/api/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Plus, Loader2, Edit, Trash2, Key, UserCheck, UserX } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [resetPasswordDialogOpen, setResetPasswordDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'operator',
  });

  const [editUser, setEditUser] = useState({
    email: '',
    full_name: '',
    role: '',
    is_active: true,
  });

  const [resetPassword, setResetPassword] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await superAdminAPI.getUsers();
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await superAdminAPI.createUser(newUser);
      toast.success('User created successfully');
      setDialogOpen(false);
      setNewUser({
        username: '',
        email: '',
        password: '',
        full_name: '',
        role: 'operator',
      });
      fetchUsers();
    } catch (error) {
      console.error('Error creating user:', error);
      toast.error(error.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    try {
      await superAdminAPI.updateUser(selectedUser.id, editUser);
      toast.success('User updated successfully');
      setEditDialogOpen(false);
      fetchUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      toast.error(error.response?.data?.detail || 'Failed to update user');
    }
  };

  const handleDeleteUser = async () => {
    try {
      await superAdminAPI.deleteUser(selectedUser.id);
      toast.success('User deleted successfully');
      setDeleteDialogOpen(false);
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  const handleResetPassword = async () => {
    try {
      await superAdminAPI.resetPassword(selectedUser.id, resetPassword);
      toast.success('Password reset successfully');
      setResetPasswordDialogOpen(false);
      setResetPassword('');
    } catch (error) {
      console.error('Error resetting password:', error);
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    }
  };

  const openEditDialog = (user) => {
    setSelectedUser(user);
    setEditUser({
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      is_active: user.is_active,
    });
    setEditDialogOpen(true);
  };

  const openDeleteDialog = (user) => {
    setSelectedUser(user);
    setDeleteDialogOpen(true);
  };

  const openResetPasswordDialog = (user) => {
    setSelectedUser(user);
    setResetPassword('');
    setResetPasswordDialogOpen(true);
  };

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'superadmin':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'admin':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'supervisor':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen" data-testid="loading-spinner">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="user-management-page">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-4xl font-bold tracking-tight">Organisation Management</h2>
          <p className="text-muted-foreground mt-2 text-lg">Manage system Organisation and their roles</p>
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-user-btn" className="rounded-full font-medium shadow-sm hover:shadow-md transition-all">
              <Plus className="w-4 h-4 mr-2" />
              Add Organisation
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Organisation</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateUser}>
              <div className="space-y-4 py-4">
                <div>
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    value={newUser.username}
                    onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                    required
                    minLength={3}
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={newUser.email}
                    onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={newUser.password}
                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                    required
                    minLength={6}
                  />
                </div>
                <div>
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input
                    id="full_name"
                    value={newUser.full_name}
                    onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="role">Role</Label>
                  <Select value={newUser.role} onValueChange={(value) => setNewUser({ ...newUser, role: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="operator">Operator</SelectItem>
                      <SelectItem value="supervisor">Supervisor</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                      <SelectItem value="superadmin">Super Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">Create User</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {users.map((user) => (
          <Card key={user.id} className="p-6 border border-border/60 hover:border-primary/20 transition-all">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-xl font-semibold">{user.full_name}</h3>
                  <Badge className={getRoleBadgeColor(user.role)}>
                    {user.role}
                  </Badge>
                  {user.is_active ? (
                    <Badge className="bg-green-100 text-green-800 border-green-200">
                      <UserCheck className="w-3 h-3 mr-1" />
                      Active
                    </Badge>
                  ) : (
                    <Badge className="bg-red-100 text-red-800 border-red-200">
                      <UserX className="w-3 h-3 mr-1" />
                      Inactive
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">@{user.username}</p>
                <p className="text-sm text-muted-foreground">{user.email}</p>
                <p className="text-xs text-muted-foreground mt-2">
                  Created: {format(new Date(user.created_at), 'PPp')}
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => openEditDialog(user)}
                  title="Edit user"
                >
                  <Edit className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => openResetPasswordDialog(user)}
                  title="Reset password"
                >
                  <Key className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="text-red-600 hover:text-red-700"
                  onClick={() => openDeleteDialog(user)}
                  title="Delete user"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Edit User Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpdateUser}>
            <div className="space-y-4 py-4">
              <div>
                <Label htmlFor="edit_email">Email</Label>
                <Input
                  id="edit_email"
                  type="email"
                  value={editUser.email}
                  onChange={(e) => setEditUser({ ...editUser, email: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit_full_name">Full Name</Label>
                <Input
                  id="edit_full_name"
                  value={editUser.full_name}
                  onChange={(e) => setEditUser({ ...editUser, full_name: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit_role">Role</Label>
                <Select value={editUser.role} onValueChange={(value) => setEditUser({ ...editUser, role: value })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="operator">Operator</SelectItem>
                    <SelectItem value="supervisor">Supervisor</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                    <SelectItem value="superadmin">Super Admin</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="edit_is_active"
                  checked={editUser.is_active}
                  onChange={(e) => setEditUser({ ...editUser, is_active: e.target.checked })}
                  className="w-4 h-4"
                />
                <Label htmlFor="edit_is_active">Active</Label>
              </div>
            </div>
            <DialogFooter>
              <Button type="submit">Update User</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the user <strong>{selectedUser?.username}</strong>. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteUser} className="bg-red-600 hover:bg-red-700">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Reset Password Dialog */}
      <Dialog open={resetPasswordDialogOpen} onOpenChange={setResetPasswordDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reset Password</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="text-sm text-muted-foreground">
              Reset password for user: <strong>{selectedUser?.username}</strong>
            </p>
            <div>
              <Label htmlFor="new_password">New Password</Label>
              <Input
                id="new_password"
                type="password"
                value={resetPassword}
                onChange={(e) => setResetPassword(e.target.value)}
                required
                minLength={6}
              />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleResetPassword}>Reset Password</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
