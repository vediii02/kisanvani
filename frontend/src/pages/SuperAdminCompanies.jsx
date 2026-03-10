import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Loader2, Building2, Search, Edit, Trash2, Plus, Package, Phone, User as UserIcon } from 'lucide-react';
import { PhoneInput } from '@/components/ui/phone-input';
import { toast } from 'sonner';
import { getErrorMessage } from '@/lib/utils';
import api from '../api/api';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';

export default function SuperAdminCompanies() {
  const [companies, setCompanies] = useState([]);
  const [organisations, setOrganisations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingCompany, setEditingCompany] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    organisation_id: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    pincode: '',
    contact_person: '',
    business_type: '',
    gst_number: '',
    registration_number: '',
    description: '',
    status: 'active',
    username: '',
    password: ''
  });

  useEffect(() => {
    fetchCompanies();
    fetchOrganisations();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await api.get('/admin/companies');
      setCompanies(response.data);
    } catch (error) {
      console.error('Error fetching companies:', error);
      toast.error('Failed to load companies');
    } finally {
      setLoading(false);
    }
  };

  const fetchOrganisations = async () => {
    try {
      const response = await api.get('/admin/organisations');
      setOrganisations(response.data.organisations || response.data || []);
    } catch (error) {
      console.error('Error fetching organisations:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error('Company name is required');
      return;
    }

    if (!formData.organisation_id) {
      toast.error('Please select an organisation');
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

    if (formData.phone) {
      const phoneRegex = /^\+91\d{10}$/;
      if (!phoneRegex.test(formData.phone)) {
        toast.error('Contact phone must be +91 followed by 10 digits');
        return;
      }
    }

    if (!editingCompany) {
      if (!formData.username.trim()) {
        toast.error('Username is required');
        return;
      }
      if (!formData.password || formData.password.length < 6) {
        toast.error('Password must be at least 6 characters');
        return;
      }
    }

    try {
      if (editingCompany) {
        await api.put(`/admin/companies/${editingCompany.id}`, formData);
        toast.success('Company updated successfully');
      } else {
        const submitData = { ...formData };
        const response = await api.post('/admin/companies', submitData);
        let successMsg = 'Company created successfully';
        if (response.data.admin_user) {
          successMsg += `. Login credentials: ${response.data.admin_user.username}`;
        }
        toast.success(successMsg);
      }
      setShowModal(false);
      resetForm();
      fetchCompanies();
    } catch (error) {
      console.error('Error saving company:', error);
      toast.error(getErrorMessage(error));
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this company?')) return;

    try {
      await api.delete(`/admin/companies/${id}`);
      toast.success('Company deleted successfully');
      fetchCompanies();
    } catch (error) {
      console.error('Error deleting company:', error);
      toast.error(getErrorMessage(error));
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      organisation_id: '',
      email: '',
      phone: '',
      address: '',
      city: '',
      state: '',
      pincode: '',
      contact_person: '',
      business_type: '',
      gst_number: '',
      registration_number: '',
      description: '',
      status: 'active',
      username: '',
      password: ''
    });
    setEditingCompany(null);
  };

  const openEditModal = (company) => {
    setEditingCompany(company);
    setFormData({
      name: company.name,
      organisation_id: company.organisation_id,
      email: company.email || '',
      phone: company.phone || '',
      address: company.address || '',
      city: company.city || '',
      state: company.state || '',
      pincode: company.pincode || '',
      contact_person: company.contact_person || '',
      business_type: company.business_type || '',
      gst_number: company.gst_number || '',
      registration_number: company.registration_number || '',
      description: company.description || '',
      status: company.status || 'active',
      username: '',
      password: ''
    });
    setShowModal(true);
  };

  const filteredCompanies = companies.filter(company =>
    company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    company.organisation_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Building2 className="h-8 w-8 text-primary" />
              Companies Management
            </h1>
            <Badge variant="secondary" className="mt-1 bg-purple-100 text-purple-700">{companies.length} Total Companies</Badge>
          </div>
          <p className="text-muted-foreground mt-2">View and manage all companies across organisations</p>
        </div>
        <Button onClick={() => setShowModal(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Add Company
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Search companies..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredCompanies.length === 0 ? (
          <Card className="col-span-full">
            <div className="flex flex-col items-center justify-center py-12 px-6">
              <Building2 className="w-12 h-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium">
                {searchTerm ? 'No companies found' : 'No companies available'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {searchTerm ? 'Try adjusting your search' : 'Create your first company to get started'}
              </p>
            </div>
          </Card>
        ) : (
          filteredCompanies.map((company) => (
            <Card key={company.id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Building2 className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{company.name}</h3>
                    <p className="text-sm text-gray-500">{company.organisation_name}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${company.status === 'active'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-red-100 text-red-700'
                  }`}>
                  {company.status === 'active' ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="space-y-2 text-sm">
                {company.contact_person && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Package className="h-4 w-4" />
                    <span>{company.contact_person}</span>
                  </div>
                )}
                {company.phone && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Phone className="h-4 w-4" />
                    <span>{company.phone}</span>
                  </div>
                )}
                <div className="pt-2 border-t">
                  <p className="text-xs text-gray-500">
                    Brands: {company.brand_count || 0} | Products: {company.product_count || 0}
                  </p>
                </div>
              </div>

              <div className="flex gap-2 mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => openEditModal(company)}
                  className="flex-1"
                >
                  <Edit className="h-4 w-4 mr-1" />
                  Edit
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDelete(company.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6 shadow-2xl">
            <h3 className="text-xl font-bold mb-4 border-b pb-2">
              {editingCompany ? 'Edit Company' : 'Create New Company'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4 max-h-[80vh] overflow-y-auto px-1 pr-3 custom-scrollbar">
              <div className="space-y-4">
                {/* Company Name */}
                <div className="space-y-1">
                  <Label>Company Name *</Label>
                  <Input
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Rasi Seeds Mumbai Branch"
                  />
                </div>

                {/* Organisation */}
                <div className="space-y-1">
                  <Label>Organisation *</Label>
                  <select
                    required
                    value={formData.organisation_id}
                    onChange={(e) => setFormData({ ...formData, organisation_id: e.target.value })}
                    className="w-full h-10 px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                  >
                    <option value="">Select Organisation</option>
                    {organisations.map((org) => (
                      <option key={org.id} value={org.id}>
                        {org.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Business Type & Contact Person */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <Label>Business Type</Label>
                    <Input
                      value={formData.business_type}
                      onChange={(e) => setFormData({ ...formData, business_type: e.target.value })}
                      placeholder="e.g., Distribution, Manufacturing"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>Contact Person</Label>
                    <Input
                      value={formData.contact_person}
                      onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                      placeholder="Manager name"
                    />
                  </div>
                </div>

                {/* Contact Phone & Contact Email */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <Label>Contact Phone</Label>
                    <PhoneInput
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>Contact Email *</Label>
                    <Input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="contact@company.com"
                    />
                  </div>
                </div>

                {/* Address */}
                <div className="space-y-1">
                  <Label>Address</Label>
                  <Input
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    placeholder="Full address"
                  />
                </div>

                {/* GST & Registration */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <Label>GST Number</Label>
                    <Input
                      value={formData.gst_number}
                      onChange={(e) => setFormData({ ...formData, gst_number: e.target.value })}
                      placeholder="GST Number"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>Registration Number</Label>
                    <Input
                      value={formData.registration_number}
                      onChange={(e) => setFormData({ ...formData, registration_number: e.target.value })}
                      placeholder="Business Registration No"
                    />
                  </div>
                </div>

                {/* State & City */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <Label>State</Label>
                    <Input
                      value={formData.state}
                      onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                      placeholder="State"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>City</Label>
                    <Input
                      value={formData.city}
                      onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                      placeholder="City"
                    />
                  </div>
                </div>

                {/* Pincode & Status */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <Label>Pincode</Label>
                    <Input
                      value={formData.pincode}
                      onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
                      placeholder="Pincode"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>Status</Label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      className="w-full h-10 px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </div>
                </div>

                {/* Description */}
                <div className="space-y-1">
                  <Label>Description</Label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full min-h-[80px] px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                    placeholder="Additional notes..."
                  />
                </div>
              </div>

              {!editingCompany && (
                <div className="space-y-4 pt-4 border-t">
                  <div className="bg-green-50/50 p-4 rounded-lg space-y-4">
                    <div className="text-sm font-semibold text-green-800">Login Access for this company (Required)</div>
                    <p className="text-xs text-green-600 -mt-2">Company will be able to login using these credentials</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <Label className="text-xs">Username *</Label>
                        <Input
                          required
                          placeholder="admin_username"
                          value={formData.username}
                          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                          className="bg-white"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs">Password *</Label>
                        <Input
                          type="password"
                          placeholder="Min 6 characters"
                          required
                          value={formData.password}
                          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                          className="bg-white"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-6 sticky bottom-0 bg-white pb-2">
                <Button type="submit" className="flex-1">
                  {editingCompany ? 'Update Company' : 'Create Company'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowModal(false);
                    resetForm();
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
