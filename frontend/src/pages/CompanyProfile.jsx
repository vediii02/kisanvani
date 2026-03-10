import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { User, Edit2, Save, X, Building, Phone, Mail, MapPin, Globe, FileText } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/api/api';

export default function CompanyProfile() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const [companyData, setCompanyData] = useState({
    name: '',
    business_type: '',
    brand_name: '',
    contact_person: '',
    phone: '',
    alternate_phone: '',
    email: '',
    address: '',
    city: '',
    state: '',
    pincode: '',
    gst_number: '',
    registration_number: '',
    website: '',
    description: '',
    status: 'active'
  });

  const [originalData, setOriginalData] = useState({});

  useEffect(() => {
    fetchCompanyProfile();
  }, []);

  const fetchCompanyProfile = async () => {
    try {
      setLoading(true);

      console.log('Fetching company profile...');
      const response = await api.get('/company/profile');
      console.log('API Response:', response);
      const profileData = response.data;
      console.log('Profile Data:', profileData);

      const newCompanyData = {
        name: profileData.name || '',
        business_type: profileData.business_type || '',
        brand_name: profileData.brand_name || '',
        contact_person: profileData.contact_person || '',
        phone: profileData.phone || '',
        alternate_phone: profileData.secondary_phone || '',
        email: profileData.email || '',
        address: profileData.address || '',
        city: profileData.city || '',
        state: profileData.state || '',
        pincode: profileData.pincode || '',
        gst_number: profileData.gst_number || '',
        registration_number: profileData.registration_number || '',
        website: profileData.website_link || '',
        description: profileData.description || '',
        status: profileData.status || 'active'
      };

      console.log('Setting companyData to:', newCompanyData);
      setCompanyData(newCompanyData);
      setOriginalData(newCompanyData);

    } catch (error) {
      console.error('Error fetching company profile:', error);
      console.error('Error response:', error.response);
      console.error('Error status:', error.response?.status);
      console.error('Error data:', error.response?.data);
      toast.error(error.response?.data?.detail || 'Failed to load company profile');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setEditing(true);
  };

  const handleCancel = () => {
    console.log('Cancel clicked - originalData:', originalData);
    setCompanyData(originalData);
    setEditing(false);
  };

  const handleInputChange = (field, value) => {
    setCompanyData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);

      // Prepare data for API - map frontend fields to backend fields
      const updateData = {
        name: companyData.name,
        business_type: companyData.business_type,
        brand_name: companyData.brand_name,
        contact_person: companyData.contact_person,
        phone: companyData.phone,
        secondary_phone: companyData.alternate_phone,
        email: companyData.email,
        address: companyData.address,
        city: companyData.city,
        state: companyData.state,
        pincode: companyData.pincode,
        gst_number: companyData.gst_number,
        registration_number: companyData.registration_number,
        website_link: companyData.website,
        description: companyData.description,
        notes: companyData.notes
      };

      // Call the actual API
      const response = await api.put('/company/profile', updateData);

      // Update local state with response data
      const updatedProfile = response.data;
      setCompanyData({
        name: updatedProfile.name || '',
        business_type: updatedProfile.business_type || '',
        brand_name: updatedProfile.brand_name || '',
        contact_person: updatedProfile.contact_person || '',
        phone: updatedProfile.phone || '',
        alternate_phone: updatedProfile.secondary_phone || '',
        email: updatedProfile.email || '',
        address: updatedProfile.address || '',
        city: updatedProfile.city || '',
        state: updatedProfile.state || '',
        pincode: updatedProfile.pincode || '',
        gst_number: updatedProfile.gst_number || '',
        registration_number: updatedProfile.registration_number || '',
        website: updatedProfile.website_link || '',
        description: updatedProfile.description || '',
        status: updatedProfile.status || 'active'
      });

      setOriginalData({
        name: updatedProfile.name || '',
        business_type: updatedProfile.business_type || '',
        brand_name: updatedProfile.brand_name || '',
        contact_person: updatedProfile.contact_person || '',
        phone: updatedProfile.phone || '',
        alternate_phone: updatedProfile.secondary_phone || '',
        email: updatedProfile.email || '',
        address: updatedProfile.address || '',
        city: updatedProfile.city || '',
        state: updatedProfile.state || '',
        pincode: updatedProfile.pincode || '',
        gst_number: updatedProfile.gst_number || '',
        registration_number: updatedProfile.registration_number || '',
        website: updatedProfile.website_link || '',
        description: updatedProfile.description || '',
        status: updatedProfile.status || 'active'
      });

      setEditing(false);
      toast.success('Company profile updated successfully!');

    } catch (error) {
      console.error('Error updating company profile:', error);
      toast.error(error.response?.data?.detail || 'Failed to update company profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading company profile...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <User className="h-8 w-8 text-primary" />
            Company Profile
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage your company information and details
          </p>
        </div>
        <div className="flex gap-2">
          {editing ? (
            <>
              <Button
                variant="outline"
                onClick={handleCancel}
                disabled={saving}
                className="flex items-center gap-2"
              >
                <X className="h-4 w-4" />
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2"
              >
                <Save className="h-4 w-4" />
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </>
          ) : (
            <Button
              onClick={handleEdit}
              className="flex items-center gap-2"
            >
              <Edit2 className="h-4 w-4" />
              Edit Profile
            </Button>
          )}
        </div>
      </div>

      {/* Status Badge */}
      <div className="mb-6">
        <Badge
          variant={companyData.status === 'active' ? 'default' : 'secondary'}
          className="text-sm"
        >
          {companyData.status === 'active' ? 'Active' : 'Inactive'}
        </Badge>
      </div>

      {/* Company Information */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building className="h-5 w-5" />
              Basic Information
            </CardTitle>
            <CardDescription>
              Company details and identification
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="name">Company Name</Label>
              <Input
                id="name"
                value={companyData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                disabled={!editing}
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="business_type">Business Type</Label>
              <Input
                id="business_type"
                value={companyData.business_type}
                onChange={(e) => handleInputChange('business_type', e.target.value)}
                disabled={!editing}
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="brand_name">Brand Name</Label>
              <Input
                id="brand_name"
                value={companyData.brand_name}
                onChange={(e) => handleInputChange('brand_name', e.target.value)}
                disabled={!editing}
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="website">Website</Label>
              <Input
                id="website"
                value={companyData.website}
                onChange={(e) => handleInputChange('website', e.target.value)}
                disabled={!editing}
                className="mt-1"
                placeholder="www.companywebsite.com"
              />
            </div>
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Phone className="h-5 w-5" />
              Contact Information
            </CardTitle>
            <CardDescription>
              How to reach your company
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="contact_person">Contact Person</Label>
              <Input
                id="contact_person"
                value={companyData.contact_person}
                onChange={(e) => handleInputChange('contact_person', e.target.value)}
                disabled={!editing}
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="phone">Phone Number</Label>
              <Input
                id="phone"
                placeholder="+919876543210"
                value={companyData.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
                disabled={!editing}
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="alternate_phone">Secondary Phone Number</Label>
              <Input
                id="alternate_phone"
                value={companyData.alternate_phone}
                onChange={(e) => handleInputChange('alternate_phone', e.target.value)}
                disabled={!editing}
                className="mt-1"
                placeholder="+919876543211"
              />
            </div>

            <div>
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                value={companyData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                disabled={!editing}
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="address">Address</Label>
              <Textarea
                id="address"
                value={companyData.address}
                onChange={(e) => handleInputChange('address', e.target.value)}
                disabled={!editing}
                className="mt-1"
                rows={3}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  value={companyData.city}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  disabled={!editing}
                  className="mt-1"
                  placeholder="Mumbai"
                />
              </div>

              <div>
                <Label htmlFor="state">State</Label>
                <Input
                  id="state"
                  value={companyData.state}
                  onChange={(e) => handleInputChange('state', e.target.value)}
                  disabled={!editing}
                  className="mt-1"
                  placeholder="Maharashtra"
                />
              </div>

              <div>
                <Label htmlFor="pincode">Pincode</Label>
                <Input
                  id="pincode"
                  value={companyData.pincode}
                  onChange={(e) => handleInputChange('pincode', e.target.value)}
                  disabled={!editing}
                  className="mt-1"
                  placeholder="400001"
                  maxLength={6}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Legal Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Legal Information
            </CardTitle>
            <CardDescription>
              Company registration and tax details
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="gst_number">GST Number</Label>
              <Input
                id="gst_number"
                value={companyData.gst_number}
                onChange={(e) => handleInputChange('gst_number', e.target.value)}
                disabled={!editing}
                className="mt-1 bg-muted"
                placeholder="27AAAPL1234C1ZV"
              />
            </div>

            <div>
              <Label htmlFor="registration_number">Registration Number</Label>
              <Input
                id="registration_number"
                value={companyData.registration_number}
                onChange={(e) => handleInputChange('registration_number', e.target.value)}
                disabled={!editing}
                className="mt-1 bg-muted"
                placeholder="ROC-123456"
              />
            </div>
          </CardContent>
        </Card>

        {/* Company Description */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="h-5 w-5" />
              Company Description
            </CardTitle>
            <CardDescription>
              Tell us about your company
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              id="description"
              value={companyData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              disabled={!editing}
              className="mt-1"
              rows={6}
              placeholder="Describe your company, products, and services..."
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
