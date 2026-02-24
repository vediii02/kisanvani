import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Building2, Plus, Edit2, Trash2, Search, Phone, Mail, MapPin, ToggleLeft, ToggleRight } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/api/api';

export default function AdminOrganisations() {
  const [organisations, setOrganisations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    plan_type: 'basic',
    phone_numbers: '',
    primary_phone: '',
    preferred_languages: 'hi',
    greeting_message: '',
    status: 'active',
    username: '',
    email: '',
    password: ''
  });

  useEffect(() => {
    fetchOrganisations();
  }, []);

  const fetchOrganisations = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/organisations');
      setOrganisations(response.data.organisations || response.data || []);
    } catch (error) {
      console.error('Error fetching organisations:', error);
      toast.error('Failed to load organisations');
      setOrganisations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.domain) {
      toast.error('Name and Domain are required');
      return;
    }
    if (!formData.username || !formData.email || !formData.password) {
      toast.error('Username, Email and Password are required for organisation login');
      return;
    }

    setLoading(true);
    try {
      await api.post('/admin/organisations', formData);
      toast.success('Organisation created successfully');
      setShowCreateModal(false);
      resetForm();
      fetchOrganisations();
    } catch (error) {
      console.error('Error creating organisation:', error);
      toast.error(error.response?.data?.detail || 'Failed to create organisation');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async () => {
    if (!formData.name || !formData.domain) {
      toast.error('Name and Domain are required');
      return;
    }

    setLoading(true);
    try {
      await api.put(`/admin/organisations/${selectedOrg.id}`, formData);
      toast.success('Organisation updated successfully');
      setShowEditModal(false);
      setSelectedOrg(null);
      resetForm();
      fetchOrganisations();
    } catch (error) {
      console.error('Error updating organisation:', error);
      toast.error(error.response?.data?.detail || 'Failed to update organisation');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (org) => {
    if (!confirm(`Are you sure you want to delete "${org.name}"?`)) {
      return;
    }

    setLoading(true);
    try {
      await api.delete(`/admin/organisations/${org.id}`);
      toast.success('Organisation deleted successfully');
      fetchOrganisations();
    } catch (error) {
      console.error('Error deleting organisation:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete organisation');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (org) => {
    const newStatus = org.status === 'active' ? 'inactive' : 'active';
    setLoading(true);
    try {
      await api.put(`/admin/organisations/${org.id}`, { ...org, status: newStatus });
      toast.success(`Organisation ${newStatus === 'active' ? 'activated' : 'deactivated'}`);
      fetchOrganisations();
    } catch (error) {
      console.error('Error toggling status:', error);
      toast.error('Failed to update status');
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = () => {
    resetForm();
    setShowCreateModal(true);
  };

  const openEditModal = (org) => {
    setSelectedOrg(org);
    setFormData({
      name: org.name || '',
      domain: org.domain || '',
      plan_type: org.plan_type || 'basic',
      phone_numbers: org.phone_numbers || '',
      primary_phone: org.primary_phone || '',
      preferred_languages: org.preferred_languages || 'hi',
      greeting_message: org.greeting_message || '',
      status: org.status || 'active'
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      domain: '',
      plan_type: 'basic',
      phone_numbers: '',
      primary_phone: '',
      preferred_languages: 'hi',
      greeting_message: '',
      status: 'active',
      username: '',
      email: '',
      password: ''
    });
  };

  const filteredOrganisations = organisations.filter(org =>
    org.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    org.domain?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Building2 className="w-8 h-8 text-primary" />
            Organisations Management
          </h1>
          <p className="text-muted-foreground mt-1">Manage all organisations in the platform</p>
        </div>
        <Button onClick={openCreateModal} className="gap-2">
          <Plus className="w-4 h-4" />
          Add Organisation
        </Button>
      </div>

      {/* Search */}
      <Card className="p-4">
        <div className="flex items-center gap-2">
          <Search className="w-5 h-5 text-muted-foreground" />
          <Input
            placeholder="Search organisations by name or domain..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1"
          />
        </div>
      </Card>

      {/* Organisations List */}
      {loading && organisations.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading organisations...</p>
        </div>
      ) : filteredOrganisations.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <Building2 className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No organisations found</h3>
            <p className="text-muted-foreground mb-4">
              {searchTerm ? 'Try adjusting your search' : 'Get started by creating your first organisation'}
            </p>
            {!searchTerm && (
              <Button onClick={openCreateModal}>
                <Plus className="w-4 h-4 mr-2" />
                Add Organisation
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredOrganisations.map((org) => (
            <Card key={org.id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <Building2 className="w-6 h-6 text-primary" />
                    <div>
                      <h3 className="text-xl font-semibold">{org.name}</h3>
                      <p className="text-sm text-muted-foreground">Domain: {org.domain}</p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                      org.status === 'active' 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {org.status || 'active'}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {org.plan_type && (
                      <div>
                        <span className="text-muted-foreground">Plan Type:</span>
                        <p className="font-medium capitalize">{org.plan_type}</p>
                      </div>
                    )}
                    {org.primary_phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-muted-foreground" />
                        <span className="font-medium">{org.primary_phone}</span>
                      </div>
                    )}
                    {org.preferred_languages && (
                      <div>
                        <span className="text-muted-foreground">Languages:</span>
                        <p className="font-medium">{org.preferred_languages}</p>
                      </div>
                    )}
                    {org.contact_person && (
                      <div>
                        <span className="text-muted-foreground">Contact Person:</span>
                        <p className="font-medium">{org.contact_person}</p>
                      </div>
                    )}
                    {org.contact_email && (
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-muted-foreground" />
                        <span className="font-medium">{org.contact_email}</span>
                      </div>
                    )}
                    {org.contact_phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-muted-foreground" />
                        <span className="font-medium">{org.contact_phone}</span>
                      </div>
                    )}
                    {org.address && (
                      <div className="col-span-2 flex items-start gap-2">
                        <MapPin className="w-4 h-4 text-muted-foreground mt-1" />
                        <span className="font-medium">{org.address}</span>
                      </div>
                    )}
                  </div>

                  {org.created_at && (
                    <p className="text-xs text-muted-foreground mt-3">
                      Created: {new Date(org.created_at).toLocaleDateString()}
                    </p>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => handleToggleStatus(org)}
                    title={org.status === 'active' ? 'Deactivate' : 'Activate'}
                  >
                    {org.status === 'active' ? (
                      <ToggleRight className="w-4 h-4 text-green-600" />
                    ) : (
                      <ToggleLeft className="w-4 h-4 text-gray-400" />
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => openEditModal(org)}
                  >
                    <Edit2 className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => handleDelete(org)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Organisation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Organisation Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Rasi Seeds Ltd"
                  required
                />
              </div>
              <div>
                <Label htmlFor="domain">Domain *</Label>
                <Input
                  id="domain"
                  value={formData.domain}
                  onChange={(e) => setFormData({ ...formData, domain: e.target.value.toLowerCase() })}
                  placeholder="e.g., rasiseeds"
                  required
                />
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
              <h3 className="font-semibold text-blue-900">Login Credentials</h3>
              <p className="text-sm text-blue-700">These credentials will be used to create an organisation admin user</p>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="username">Username *</Label>
                  <Input
                    id="username"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    placeholder="e.g., rasiadmin"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="admin@rasiseeds.com"
                    required
                  />
                </div>
              </div>
              
              <div>
                <Label htmlFor="password">Password *</Label>
                <Input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Enter secure password"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="plan_type">Plan Type</Label>
                <Select value={formData.plan_type} onValueChange={(value) => setFormData({ ...formData, plan_type: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basic">Basic</SelectItem>
                    <SelectItem value="premium">Premium</SelectItem>
                    <SelectItem value="enterprise">Enterprise</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="status">Status</Label>
                <Select value={formData.status} onValueChange={(value) => setFormData({ ...formData, status: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="phone_numbers">Phone Numbers</Label>
              <Input
                id="phone_numbers"
                value={formData.phone_numbers}
                onChange={(e) => setFormData({ ...formData, phone_numbers: e.target.value })}
                placeholder="Comma-separated phone numbers"
              />
            </div>

            <div>
              <Label htmlFor="primary_phone">Primary Phone</Label>
              <Input
                id="primary_phone"
                value={formData.primary_phone}
                onChange={(e) => setFormData({ ...formData, primary_phone: e.target.value })}
                placeholder="+91 1234567890"
              />
            </div>

            <div>
              <Label htmlFor="preferred_languages">Preferred Languages</Label>
              <Input
                id="preferred_languages"
                value={formData.preferred_languages}
                onChange={(e) => setFormData({ ...formData, preferred_languages: e.target.value })}
                placeholder="e.g., hi,en,te"
              />
            </div>

            <div>
              <Label htmlFor="greeting_message">Greeting Message</Label>
              <Input
                id="greeting_message"
                value={formData.greeting_message}
                onChange={(e) => setFormData({ ...formData, greeting_message: e.target.value })}
                placeholder="Welcome message for callers"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={loading}>
              {loading ? 'Creating...' : 'Create Organisation'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Organisation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_name">Organisation Name *</Label>
                <Input
                  id="edit_name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label htmlFor="edit_domain">Domain *</Label>
                <Input
                  id="edit_domain"
                  value={formData.domain}
                  onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                  placeholder="e.g., rasi-seeds"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_plan_type">Plan Type</Label>
                <Select value={formData.plan_type} onValueChange={(value) => setFormData({ ...formData, plan_type: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basic">Basic</SelectItem>
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="enterprise">Enterprise</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="edit_status">Status</Label>
                <Select value={formData.status} onValueChange={(value) => setFormData({ ...formData, status: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                    <SelectItem value="suspended">Suspended</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="edit_primary_phone">Primary Phone (for farmers to call)</Label>
              <Input
                id="edit_primary_phone"
                value={formData.primary_phone}
                onChange={(e) => setFormData({ ...formData, primary_phone: e.target.value })}
                placeholder="e.g., 09513886363"
              />
            </div>

            <div>
              <Label htmlFor="edit_phone_numbers">Additional Phone Numbers (comma-separated)</Label>
              <Input
                id="edit_phone_numbers"
                value={formData.phone_numbers}
                onChange={(e) => setFormData({ ...formData, phone_numbers: e.target.value })}
                placeholder="e.g., 9876543210, 9876543211"
              />
            </div>

            <div>
              <Label htmlFor="edit_preferred_languages">Preferred Languages</Label>
              <Select value={formData.preferred_languages} onValueChange={(value) => setFormData({ ...formData, preferred_languages: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hi">Hindi (हिन्दी)</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="hi,en">Hindi + English</SelectItem>
                  <SelectItem value="mr">Marathi (मराठी)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="edit_greeting_message">Greeting Message (for AI voice)</Label>
              <Input
                id="edit_greeting_message"
                value={formData.greeting_message}
                onChange={(e) => setFormData({ ...formData, greeting_message: e.target.value })}
                placeholder="e.g., Namaste, aap Rasi Seeds Kisan Sahayak AI se baat kar rahe hain"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditModal(false)}>Cancel</Button>
            <Button onClick={handleEdit} disabled={loading}>
              {loading ? 'Updating...' : 'Update Organisation'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
