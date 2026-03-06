import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Building2, Plus, Edit2, Trash2, Search, Phone, Mail, MapPin, Users, Package } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/api/api';

export default function OrganisationCompanies() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    business_type: '',
    contact_person: '',
    email: '',
    phone: '',
    address: '',
    gst_number: '',
    registration_number: '',
    status: 'active',
    max_company_users: 5,
    max_products: 100,
    notes: '',
    username: '',
    password: '',
    login_email: ''
  });

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const response = await api.get('/organisation/companies');
      setCompanies(response.data.companies || response.data || []);
    } catch (error) {
      console.error('Error fetching companies:', error);
      toast.error('Failed to load companies');
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.name) {
      toast.error('Company name is required');
      return;
    }

    if (!formData.email) {
      toast.error('Contact Email is required');
      return;
    }
    if (!formData.login_email) {
      toast.error('Login Email is required for login access');
      return;
    }
    if (formData.email !== formData.login_email) {
      toast.error('Login Email must be the same as Contact Email');
      return;
    }
    if (!formData.password) {
      toast.error('Password is required for login access');
      return;
    }
    if (formData.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setLoading(true);
    try {
      const submitData = { ...formData };
      submitData.username = formData.login_email; // Username = Email
      delete submitData.login_email;

      await api.post('/organisation/companies', submitData);
      toast.success('Company and user account created successfully! Login with email: ' + formData.email);
      setShowCreateModal(false);
      resetForm();
      fetchCompanies();
    } catch (error) {
      console.error('Error creating company:', error);

      // Handle validation errors
      let errorMessage = 'Failed to create company';
      if (error.response?.data) {
        const data = error.response.data;
        if (typeof data.detail === 'string') {
          errorMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
          // FastAPI validation errors
          errorMessage = data.detail.map(err => {
            const location = err.loc ? (Array.isArray(err.loc) ? err.loc.join('.') : String(err.loc)) : '';
            const message = err.msg ? String(err.msg) : 'Validation error';
            return location ? `${location}: ${message}` : message;
          }).join(', ');
        } else if (data.message) {
          errorMessage = data.message;
        }
      } else if (error.message) {
        // Fallback for network errors like 504 Gateway Timeout
        errorMessage = `Network Error: ${error.message}`;
        if (error.response?.status === 504 || error.message.includes('504') || error.message.includes('timeout')) {
          errorMessage = 'Server timeout: The operation took too long. Please check your connection or try again.';
        }
      }
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async () => {
    if (!formData.name) {
      toast.error('Company name is required');
      return;
    }

    setLoading(true);
    try {
      await api.put(`/organisation/companies/${selectedCompany.id}`, formData);
      toast.success('Company updated successfully');
      setShowEditModal(false);
      setSelectedCompany(null);
      resetForm();
      fetchCompanies();
    } catch (error) {
      console.error('Error updating company:', error);

      // Handle validation errors
      let errorMessage = 'Failed to update company';
      if (error.response?.data) {
        const data = error.response.data;
        if (typeof data.detail === 'string') {
          errorMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
          // FastAPI validation errors
          errorMessage = data.detail.map(err => {
            const location = err.loc ? (Array.isArray(err.loc) ? err.loc.join('.') : String(err.loc)) : '';
            const message = err.msg ? String(err.msg) : 'Validation error';
            return location ? `${location}: ${message}` : message;
          }).join(', ');
        } else if (data.message) {
          errorMessage = data.message;
        }
      }
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (company) => {
    if (!confirm(`Are you sure you want to delete "${company.name}"?`)) {
      return;
    }

    setLoading(true);
    try {
      await api.delete(`/organisation/companies/${company.id}`);
      toast.success('Company deleted successfully');
      fetchCompanies();
    } catch (error) {
      console.error('Error deleting company:', error);
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = () => {
    resetForm();
    setShowCreateModal(true);
  };

  const openEditModal = (company) => {
    setSelectedCompany(company);
    setFormData({
      name: company.name || '',
      business_type: company.business_type || '',
      brand_name: company.brand_name || '',
      contact_person: company.contact_person || '',
      email: company.email || '',
      phone: company.phone || '',
      address: company.address || '',
      gst_number: company.gst_number || '',
      registration_number: company.registration_number || '',
      status: company.status || 'active',
      state: company.state || '',
      city: company.city || '',
      pincode: company.pincode || '',
      notes: company.notes || ''
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      business_type: '',
      brand_name: '',
      contact_person: '',
      email: '',
      phone: '',
      address: '',
      gst_number: '',
      registration_number: '',
      status: 'active',
      state: '',
      city: '',
      pincode: '',
      notes: '',
      username: '',
      password: '',
      login_email: ''
    });
  };

  const filteredCompanies = companies.filter(company =>
    company.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    company.brand_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    company.contact_person?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Building2 className="w-8 h-8 text-primary" />
            Companies Management
          </h1>
          <p className="text-muted-foreground mt-1">Manage companies in your organisation</p>
        </div>
        <Button onClick={openCreateModal} className="gap-2">
          <Plus className="w-4 h-4" />
          Add Company
        </Button>
      </div>

      {/* Search */}
      <Card className="p-4">
        <div className="flex items-center gap-2">
          <Search className="w-5 h-5 text-muted-foreground" />
          <Input
            placeholder="Search companies by name, brand, or contact person..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1"
          />
        </div>
      </Card>

      {/* Companies List */}
      {loading && companies.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading companies...</p>
        </div>
      ) : filteredCompanies.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <Building2 className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No companies found</h3>
            <p className="text-muted-foreground mb-4">
              {searchTerm ? 'Try adjusting your search' : 'Get started by creating your first company'}
            </p>
            {!searchTerm && (
              <Button onClick={openCreateModal}>
                <Plus className="w-4 h-4 mr-2" />
                Add Company
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredCompanies.map((company) => (
            <Card key={company.id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <Building2 className="w-6 h-6 text-primary" />
                    <div>
                      <h3 className="text-xl font-semibold">{company.name}</h3>
                      {company.business_type && (
                        <p className="text-sm text-muted-foreground">{company.business_type}</p>
                      )}
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${company.status === 'active'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-700'
                      }`}>
                      {company.status || 'active'}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {company.business_type && (
                      <div>
                        <span className="text-muted-foreground">Business Type:</span>
                        <p className="font-medium">{company.business_type}</p>
                      </div>
                    )}
                    {company.contact_person && (
                      <div>
                        <span className="text-muted-foreground">Contact Person:</span>
                        <p className="font-medium">{company.contact_person}</p>
                      </div>
                    )}
                    {company.email && (
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-muted-foreground" />
                        <span className="font-medium">{company.email}</span>
                      </div>
                    )}
                    {company.phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-muted-foreground" />
                        <span className="font-medium">{company.phone}</span>
                      </div>
                    )}
                    {company.gst_number && (
                      <div>
                        <span className="text-muted-foreground">GST Number:</span>
                        <p className="font-medium">{company.gst_number}</p>
                      </div>
                    )}
                    {company.registration_number && (
                      <div>
                        <span className="text-muted-foreground">Registration No:</span>
                        <p className="font-medium">{company.registration_number}</p>
                      </div>
                    )}
                    {company.address && (
                      <div className="col-span-2 flex items-start gap-2">
                        <MapPin className="w-4 h-4 text-muted-foreground mt-1" />
                        <span className="font-medium">{company.address}</span>
                      </div>
                    )}
                  </div>

                  {/* <div className="flex gap-4 mt-4 text-sm">
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4 text-muted-foreground" />
                      <span>Max Company Users: <strong>{company.max_company_users || 5}</strong></span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Package className="w-4 h-4 text-muted-foreground" />
                      <span>Max Products: <strong>{company.max_products || 100}</strong></span>
                    </div>
                  </div> */}

                  {company.created_at && (
                    <p className="text-xs text-muted-foreground mt-3">
                      Created: {new Date(company.created_at).toLocaleDateString()}
                    </p>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => openEditModal(company)}
                  >
                    <Edit2 className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => handleDelete(company)}
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
            <DialogTitle>Create New Company</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Company Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Rasi Seeds Mumbai Branch"
                  required
                />
              </div>
              <div>
                <Label htmlFor="brand_name">Brand Name</Label>
                <Input
                  id="brand_name"
                  value={formData.brand_name}
                  onChange={(e) => setFormData({ ...formData, brand_name: e.target.value })}
                  placeholder="Trading name or brand"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="business_type">Business Type</Label>
                <Input
                  id="business_type"
                  value={formData.business_type}
                  onChange={(e) => setFormData({ ...formData, business_type: e.target.value })}
                  placeholder="e.g., Distribution, Manufacturing, Retailer"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="contact_person">Contact Person</Label>
                <Input
                  id="contact_person"
                  value={formData.contact_person}
                  onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                  placeholder="Manager name"
                />
              </div>
              <div>
                <Label htmlFor="phone">Contact Phone</Label>
                <Input
                  id="phone"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+91 1234567890"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="email">Contact Email *</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="contact@company.com"
                required
              />
            </div>

            <div>
              <Label htmlFor="address">Address</Label>
              <Input
                id="address"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                placeholder="Full address"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="gst_number">GST Number</Label>
                <Input
                  id="gst_number"
                  value={formData.gst_number}
                  onChange={(e) => setFormData({ ...formData, gst_number: e.target.value })}
                  placeholder="GST Number"
                />
              </div>
              <div>
                <Label htmlFor="registration_number">Registration Number</Label>
                <Input
                  id="registration_number"
                  value={formData.registration_number}
                  onChange={(e) => setFormData({ ...formData, registration_number: e.target.value })}
                  placeholder="Business Registration No"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="state">State</Label>
                <Input
                  id="state"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  placeholder="State"
                />
              </div>
              <div>
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  placeholder="City"
                />
              </div>
              <div>
                <Label htmlFor="pincode">Pincode</Label>
                <Input
                  id="pincode"
                  value={formData.pincode}
                  onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
                  placeholder="Pincode"
                />
              </div>
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

            <div>
              <Label htmlFor="notes">Description</Label>
              <Input
                id="notes"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Additional notes..."
              />
            </div>

            {/* Login Access Section */}
            <div className="border-t pt-4 mt-4">
              <div className="mb-4">
                <Label className="font-semibold text-primary">
                  Login Access for this company (Required)
                </Label>
              </div>

              <div className="space-y-4 pl-6 border-l-2 border-primary/20">
                <p className="text-sm text-muted-foreground mb-3">
                  Company will be able to login using their email address
                </p>
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="login_email">Login Email * (This will be the username)</Label>
                    <Input
                      id="login_email"
                      type="email"
                      value={formData.login_email}
                      onChange={(e) => setFormData({ ...formData, login_email: e.target.value })}
                      placeholder="company@example.com"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="password">Password *</Label>
                    <Input
                      id="password"
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      placeholder="Minimum 6 characters"
                      required
                    />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  💡 Company will login with: <strong>{formData.login_email || 'their email'}</strong>
                </p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={loading}>
              {loading ? 'Creating...' : 'Create Company'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Company</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_name">Company Name *</Label>
                <Input
                  id="edit_name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label htmlFor="edit_brand_name">Brand Name</Label>
                <Input
                  id="edit_brand_name"
                  value={formData.brand_name}
                  onChange={(e) => setFormData({ ...formData, brand_name: e.target.value })}
                  placeholder="Trading name or brand"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_business_type">Business Type</Label>
                <Input
                  id="edit_business_type"
                  value={formData.business_type}
                  onChange={(e) => setFormData({ ...formData, business_type: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_contact_person">Contact Person</Label>
                <Input
                  id="edit_contact_person"
                  value={formData.contact_person}
                  onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit_phone">Contact Phone</Label>
                <Input
                  id="edit_phone"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="edit_email">Contact Email</Label>
              <Input
                id="edit_email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>

            <div>
              <Label htmlFor="edit_address">Address</Label>
              <Input
                id="edit_address"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_gst_number">GST Number</Label>
                <Input
                  id="edit_gst_number"
                  value={formData.gst_number}
                  onChange={(e) => setFormData({ ...formData, gst_number: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit_registration_number">Registration Number</Label>
                <Input
                  id="edit_registration_number"
                  value={formData.registration_number}
                  onChange={(e) => setFormData({ ...formData, registration_number: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_state">State</Label>
                <Input
                  id="edit_state"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  placeholder="State"
                />
              </div>
              <div>
                <Label htmlFor="edit_city">City</Label>
                <Input
                  id="edit_city"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  placeholder="City"
                />
              </div>
              <div>
                <Label htmlFor="edit_pincode">Pincode</Label>
                <Input
                  id="edit_pincode"
                  value={formData.pincode}
                  onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
                  placeholder="Pincode"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_max_company_users">Max Company Users</Label>
                <Input
                  id="edit_max_company_users"
                  type="number"
                  value={formData.max_company_users}
                  onChange={(e) => setFormData({ ...formData, max_company_users: parseInt(e.target.value) || 5 })}
                />
              </div>
              <div>
                <Label htmlFor="edit_max_products">Max Products</Label>
                <Input
                  id="edit_max_products"
                  type="number"
                  value={formData.max_products}
                  onChange={(e) => setFormData({ ...formData, max_products: parseInt(e.target.value) || 100 })}
                />
              </div>
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
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="edit_notes">Description</Label>
              <Input
                id="edit_notes"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Additional notes..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditModal(false)}>Cancel</Button>
            <Button onClick={handleEdit} disabled={loading}>
              {loading ? 'Updating...' : 'Update Company'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div >
  );
}
