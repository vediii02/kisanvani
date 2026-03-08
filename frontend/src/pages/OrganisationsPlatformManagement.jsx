// Organisation Platform Management - Super Admin View
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Package,
  Phone,
  PhoneCall,
  Users,
  ToggleLeft,
  ToggleRight,
  AlertTriangle,
  CheckCircle,
  Eye,
  TrendingUp,
  Plus,
  Edit2,
  Trash2,
  Search,
  Mail,
  MapPin,
  Globe
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import { getErrorMessage } from '@/lib/utils';
import api from '../api/api';

export default function OrganisationsPlatformManagement() {
  const navigate = useNavigate();
  const [organisations, setOrganisations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [processingId, setProcessingId] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone_numbers: '',
    address: '',
    description: '',
    website_url: '',
    username: '',
    admin_password: '',
    auto_import_products: false,
    state: '',
    city: '',
    pincode: ''
  });

  useEffect(() => {
    fetchOrganisations();
  }, []);

  const fetchOrganisations = async () => {
    try {
      setLoading(true);
      const response = await api.get('/superadmin/organisations/stats');
      setOrganisations(response.data);
    } catch (error) {
      console.error('Error fetching organisations:', error);
      toast.error('Failed to load organisations');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      email: '',
      phone_numbers: '',
      address: '',
      description: '',
      website_url: '',
      username: '',
      admin_password: '',
      auto_import_products: false,
      state: '',
      city: '',
      pincode: ''
    });
  };

  const handleCreate = async () => {
    if (!formData.name.trim()) {
      toast.error('Organisation name is required');
      return;
    }

    if (!formData.email.trim()) {
      toast.error('Email is required');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      toast.error('Please enter a valid email address');
      return;
    }

    if (!formData.username || !formData.admin_password) {
      toast.error('Login credentials missing');
      return;
    }

    setLoading(true);
    try {
      const submitData = { ...formData };

      const response = await api.post('/superadmin/organisations', submitData);

      let successMsg = `Organisation "${formData.name}" created successfully!`;
      if (response.data.admin_user) {
        successMsg += ` Login with: ${response.data.admin_user.username}`;
      }

      toast.success(successMsg);
      setShowCreateModal(false);
      resetForm();
      fetchOrganisations();
    } catch (error) {
      console.error('Error creating organisation:', error);
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async () => {
    if (!formData.name.trim()) {
      toast.error('Organisation name is required');
      return;
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      toast.error('Please enter a valid email address');
      return;
    }

    setLoading(true);
    try {
      await api.put(`/superadmin/organisations/${selectedOrg.id}`, formData);
      toast.success('Organisation updated successfully');
      setShowEditModal(false);
      setSelectedOrg(null);
      resetForm();
      fetchOrganisations();
    } catch (error) {
      console.error('Error updating organisation:', error);
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (org) => {
    if (!window.confirm(`Are you sure you want to delete "${org.name}"? This action cannot be undone.`)) {
      return;
    }

    setLoading(true);
    try {
      await api.delete(`/superadmin/organisations/${org.id}`);
      toast.success('Organisation deleted successfully');
      fetchOrganisations();
    } catch (error) {
      console.error('Error deleting organisation:', error);
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const toggleOrganisationStatus = async (orgId, currentStatus) => {
    if (!window.confirm(
      currentStatus ?
        'Inactive this organisation? All their services will be disabled.' :
        'Activate this organisation? Their services will resume.'
    )) {
      return;
    }

    try {
      setProcessingId(orgId);
      await api.patch(`/superadmin/organisations/${orgId}/status`, {
        is_active: !currentStatus
      });

      toast.success(`Organisation ${currentStatus ? 'inactive' : 'activated'} successfully`);
      fetchOrganisations();
    } catch (error) {
      console.error('Error toggling organisation status:', error);
      toast.error('Failed to update organisation status');
    } finally {
      setProcessingId(null);
    }
  };

  const filteredOrgs = organisations.filter(org =>
    org.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    org.id.toString().includes(searchTerm)
  );

  if (loading && organisations.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading organisations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-primary/10 rounded-xl shadow-sm border border-primary/20">
            <Building2 className="h-8 w-8 text-primary" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight text-gray-900">Organisation Management</h1>
              <Badge variant="secondary" className="mt-1 bg-purple-100 text-purple-700">{organisations.length} Total Organisations</Badge>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search organisations..."
              className="pl-9 w-64 h-11"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button
            onClick={() => {
              resetForm();
              setShowCreateModal(true);
            }}
            size="lg"
            className="h-11 shadow-lg bg-green-600 hover:bg-green-700 text-white"
          >
            <Plus className="h-5 w-5 mr-2" />
            Add Organisation
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-5 border-none shadow-sm bg-blue-50/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-600/70 text-sm font-medium">Total Organisations</p>
              <p className="text-3xl font-bold text-blue-900">{organisations.length}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Building2 className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </Card>

        <Card className="p-5 border-none shadow-sm bg-green-50/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-600/70 text-sm font-medium">Active Orgs</p>
              <p className="text-3xl font-bold text-green-900">
                {organisations.filter(o => o.is_active).length}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </Card>

        <Card className="p-5 border-none shadow-sm bg-purple-50/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-600/70 text-sm font-medium">Inactive Orgs</p>
              <p className="text-3xl font-bold text-purple-900">
                {organisations.filter(o => !o.is_active).length}
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Organisations Table */}
      <Card className="overflow-hidden border-none shadow-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50/50">
              <tr>
                <th className="x-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Organisation
                </th>
                <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Status
                </th>

                <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Calls
                </th>
                <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {filteredOrgs.map((org) => (
                <tr key={org.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className={`p-2 rounded-lg ${org.is_active ? 'bg-blue-50 text-blue-600' : 'bg-gray-100 text-gray-400'}`}>
                        <Building2 className="h-5 w-5" />
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-semibold text-gray-900">{org.name}</div>
                        <div className="text-xs text-muted-foreground">ID: {org.id}</div>
                      </div>
                    </div>
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${org.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      org.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                      }`}>
                      {org.status === 'rejected' ? 'Rejected' : org.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>



                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className="text-sm font-medium text-gray-900">{org.call_count || 0}</span>
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => navigate(`/superadmin/organisations-platform/${org.id}`)}
                        title="View Details"
                      >
                        <Eye className="h-4 w-4 text-blue-500" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => {
                          setSelectedOrg(org);
                          setFormData({
                            name: org.name || '',
                            email: org.email || '',
                            phone_numbers: org.phone_numbers || '',
                            address: org.address || '',
                            description: org.description || '',
                            website_url: org.website_url || '',
                            admin_password: '',
                            username: org.admin_username || '',
                            is_active: org.is_active,
                            state: org.state || '',
                            city: org.city || '',
                            pincode: org.pincode || ''
                          });
                          setShowEditModal(true);
                        }}
                        title="Edit"
                      >
                        <Edit2 className="h-4 w-4 text-gray-500" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        disabled={processingId === org.id}
                        onClick={() => toggleOrganisationStatus(org.id, org.is_active)}
                        title={org.is_active ? 'Inactive' : 'Active'}
                      >
                        {org.is_active ? <ToggleRight className="h-5 w-5 text-green-500" /> : <ToggleLeft className="h-5 w-5 text-gray-400" />}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(org)}
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredOrgs.length === 0 && (
          <div className="p-12 text-center bg-white">
            <Search className="h-12 w-12 text-gray-200 mx-auto mb-4" />
            <p className="text-muted-foreground text-lg">No matching organisations found</p>
          </div>
        )}
      </Card>

      {/* Create Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-2xl">
              <Plus className="h-6 w-6 text-green-600" />
              Add New Organisation
            </DialogTitle>
            <DialogDescription>
              Enter the organisation details and set up an administrator account.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 pt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Organisation Name *</Label>
                <Input
                  placeholder="e.g., Kisan Advisory Service"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Organisation Email *</Label>
                <Input
                  type="email"
                  placeholder="admin@organisation.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Phone className="h-4 w-4 text-blue-500" />
                  Contact Number
                </Label>
                <Input
                  type="tel"
                  placeholder="+91..."
                  value={formData.phone_numbers}
                  onChange={(e) => setFormData({ ...formData, phone_numbers: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Globe className="h-4 w-4 text-blue-500" />
                  Website URL
                </Label>
                <Input
                  placeholder="https://..."
                  value={formData.website_url}
                  onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-blue-500" />
                Address
              </Label>
              <Input
                placeholder="Full office address"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label>Description</Label>
              <textarea
                className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="Brief description about the organisation..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  State
                </Label>
                <Input
                  type="text"
                  placeholder="State"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  City
                </Label>
                <Input
                  placeholder="City"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                />
              </div>
            </div>

            <div>
              <Label>Pincode</Label>
              <Input
                placeholder="Pincode"
                value={formData.pincode}
                onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
              />
            </div>

            <div className="space-y-4 pt-4 border-t">
              <div>
                <label>
                  Create login access for this organisation
                </label>
              </div>
              <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                <div className="space-y-2">
                  <Label>Username *</Label>
                  <Input
                    placeholder="admin_username"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Password *</Label>
                  <Input
                    type="password"
                    placeholder="Min 6 characters"
                    value={formData.admin_password}
                    onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
                    required
                  />
                </div>
              </div>
            </div>


          </div>

          <DialogFooter className="pt-6">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={loading} className="bg-green-600 hover:bg-green-700 text-white">
              {loading ? "Creating..." : "Create Organisation"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-2xl">
              <Edit2 className="h-6 w-6 text-blue-600" />
              Edit Organisation
            </DialogTitle>
            <DialogDescription>
              Modify the organisation's profile and administrative settings.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label>Organisation Name</Label>
              <Input
                value={formData.name}
                onChange={(e) => {
                  const newName = e.target.value;
                  setFormData({
                    ...formData,
                    name: newName,
                    username: newName.trim().toLowerCase().replace(/\s+/g, '_')
                  });
                }}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Contact Number</Label>
                <Input
                  type="number"
                  value={formData.phone_numbers}
                  onChange={(e) => setFormData({ ...formData, phone_numbers: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Address</Label>
              <Input
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Website URL</Label>
              <Input
                placeholder="https://..."
                value={formData.website_url}
                onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
              />
            </div>
          </div>
          <div className="space-y-4 pt-4 border-t">
            <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
              <div className="space-y-2">
                <Label>Admin Username *</Label>
                <Input
                  placeholder="admin_username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Admin Password (leave blank to keep current)</Label>
                <Input
                  type="password"
                  placeholder="New password"
                  value={formData.admin_password}
                  onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
                />
              </div>
            </div>
          </div>

          <DialogFooter className="pt-6">
            <Button variant="outline" onClick={() => setShowEditModal(false)}>Cancel</Button>
            <Button onClick={handleEdit} disabled={loading}>
              {loading ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
