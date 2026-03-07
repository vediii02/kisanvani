import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { User, Edit2, Save, X, Building, Phone, Mail, MapPin, Globe, FileText, Smartphone } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/api/api';

export default function OrganisationProfile() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone_numbers: '',
    secondary_phone: '',
    address: '',
    city: '',
    state: '',
    pincode: '',
    website_link: '',
    description: ''
  });

  // Keep originalData for cancel functionality, but update its structure
  const [originalData, setOriginalData] = useState({});
  // Keep status and plan_type separate as they are not editable via formData
  const [status, setStatus] = useState('active');
  const [planType, setPlanType] = useState('basic');


  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const response = await api.get('/organisations/profile');
      const data = response.data;

      const newFormData = {
        name: data.name || '',
        email: data.email || '',
        phone_numbers: data.phone_numbers || '',
        secondary_phone: data.secondary_phone || '',
        address: data.address || '',
        city: data.city || '',
        state: data.state || '',
        pincode: data.pincode || '',
        website_link: data.website_link || '',
        description: data.description || ''
      };

      setFormData(newFormData);
      setOriginalData(newFormData); // Store for cancel
      setStatus(data.status || 'active');
      setPlanType(data.plan_type || 'basic');
    } catch (error) {
      console.error('Error fetching organisation profile:', error);
      toast.error(error.response?.data?.detail || 'Failed to load organisation profile');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setEditing(true);
  };

  const handleCancel = () => {
    setFormData(originalData); // Revert to original data
    setEditing(false);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);

      const updateData = {
        name: formData.name,
        email: formData.email,
        phone_numbers: formData.phone_numbers,
        secondary_phone: formData.secondary_phone,
        address: formData.address,
        city: formData.city,
        state: formData.state,
        pincode: formData.pincode,
        website_link: formData.website_link,
        description: formData.description
      };

      const response = await api.put('/organisations/profile', updateData);
      const updatedProfile = response.data;

      const savedData = {
        name: updatedProfile.name || '',
        email: updatedProfile.email || '',
        phone_numbers: updatedProfile.phone_numbers || '',
        secondary_phone: updatedProfile.secondary_phone || '',
        address: updatedProfile.address || '',
        city: updatedProfile.city || '',
        state: updatedProfile.state || '',
        pincode: updatedProfile.pincode || '',
        website_link: updatedProfile.website_link || '',
        description: updatedProfile.description || ''
      };

      setFormData(savedData);
      setOriginalData(savedData);
      setEditing(false);
      toast.success('Organisation profile updated successfully!');
    } catch (error) {
      console.error('Error updating organisation profile:', error);
      toast.error(error.response?.data?.detail || 'Failed to update organisation profile');
    } finally {
      setSaving(false);
    }
  };


  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900 mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading profile...</p>
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
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <User className="h-8 w-8 text-primary" />
            Organisation Profile
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage your organisation information and public details
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
                className="bg-slate-900 hover:bg-slate-800 flex items-center gap-2 text-white"
              >
                <Save className="h-4 w-4" />
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </>
          ) : (
            <Button
              onClick={handleEdit}
              className="bg-slate-900 hover:bg-slate-800 flex items-center gap-2 text-white"
            >
              <Edit2 className="h-4 w-4" />
              Edit Profile
            </Button>
          )}
        </div>
      </div>

      {/* Hero Status Card */}
      <Card className="mb-6 overflow-hidden border border-slate-200 shadow-sm">
        <div className="bg-slate-50 p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="p-4 bg-white rounded-2xl shadow-sm border border-slate-100">
                <Building className="h-10 w-10 text-slate-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900">{formData.name || 'Organisation Name'}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <Badge className="bg-slate-200 text-slate-700 hover:bg-slate-300 border-none">
                    {planType?.toUpperCase() || 'BASIC'} PLAN
                  </Badge>
                  <Badge className={`${status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'} border-none`}>
                    {status?.toUpperCase()}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Basic Information */}
        <Card className="shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-900">
              <User className="h-5 w-5 text-slate-500" />
              Basic Information
            </CardTitle>
            <CardDescription>
              Organisation identification and branding
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="name">Organisation Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                disabled={!editing}
                className="mt-1 focus-visible:ring-slate-400"
              />
            </div>

            <div>
              <Label htmlFor="email">Email Address</Label>
              <div className="relative mt-1">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  disabled={!editing}
                  className="pl-10 focus-visible:ring-slate-400"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="website_link">Website URL</Label>
              <div className="relative mt-1">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  id="website_link"
                  value={formData.website_link}
                  onChange={(e) => handleInputChange('website_link', e.target.value)}
                  disabled={!editing}
                  className="pl-10 focus-visible:ring-slate-400"
                  placeholder="https://example.com"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card className="shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-900">
              <Smartphone className="h-5 w-5 text-slate-500" />
              Contact Details
            </CardTitle>
            <CardDescription>
              Registered phone contacts for call routing
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-4">
              <div>
                <Label htmlFor="phone_numbers">Organisation Phone Number</Label>
                <div className="relative mt-1">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    id="phone_numbers"
                    value={formData.phone_numbers}
                    onChange={(e) => handleInputChange('phone_numbers', e.target.value)}
                    disabled={!editing}
                    className="pl-10 focus-visible:ring-slate-400"
                    placeholder="+91 83109 01234"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="secondary_phone">Secondary Phone Number</Label>
                <div className="relative mt-1">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    id="secondary_phone"
                    value={formData.secondary_phone}
                    onChange={(e) => handleInputChange('secondary_phone', e.target.value)}
                    disabled={!editing}
                    className="pl-10 focus-visible:ring-slate-400"
                    placeholder="+91 98765 43210"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Address and Location */}
        <Card className="shadow-md md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-900">
              <MapPin className="h-5 w-5 text-slate-500" />
              Location Information
            </CardTitle>
            <CardDescription>
              Physical office address and regional details
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="address">Full Address</Label>
              <Textarea
                id="address"
                value={formData.address}
                onChange={(e) => handleInputChange('address', e.target.value)}
                disabled={!editing}
                className="mt-1 min-h-[80px] focus-visible:ring-slate-400"
                placeholder="123 Business Park, Sector 45..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  placeholder="indore"
                  value={formData.city}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  disabled={!editing}
                  className="mt-1 focus-visible:ring-slate-400"
                />
              </div>

              <div>
                <Label htmlFor="state">State</Label>
                <Input
                  id="state"
                  placeholder="Madhya Pradesh"
                  value={formData.state}
                  onChange={(e) => handleInputChange('state', e.target.value)}
                  disabled={!editing}
                  className="mt-1 focus-visible:ring-slate-400"
                />
              </div>

              <div>
                <Label htmlFor="pincode">Pincode</Label>
                <Input
                  id="pincode"
                  placeholder="452001"
                  value={formData.pincode}
                  onChange={(e) => handleInputChange('pincode', e.target.value)}
                  disabled={!editing}
                  className="mt-1 focus-visible:ring-slate-400"
                  maxLength={6}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Description */}
        <Card className="shadow-md md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-900">
              <FileText className="h-5 w-5 text-slate-500" />
              Organisation Bio
            </CardTitle>
            <CardDescription>
              Brief description for public profile
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              disabled={!editing}
              className="mt-1 min-h-[120px] focus-visible:ring-slate-400"
              placeholder="Tell us about your mission, services, and achievements..."
            />
          </CardContent>
        </Card>
      </div>

      {/* Footer Info */}
      <div className="mt-8 text-center text-sm text-muted-foreground bg-slate-50 rounded-lg p-4 border border-dashed border-slate-200">
        <p>Tip: Ensure your contact details and address are accurate so customers can reach you easily.</p>
        <p className="mt-1 italic">Enterprise features can be requested through support.</p>
      </div>
    </div>
  );
}
