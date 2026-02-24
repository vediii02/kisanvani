import React, { useState, useEffect } from 'react';
import { Plus, Loader2, Building2, Phone as PhoneIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { organisationAPI } from '@/api/api';

export default function OrganisationManagement() {
  const [organisations, setOrganisations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [phoneDialogOpen, setPhoneDialogOpen] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState();
  const [newOrg, setNewOrg] = useState({
    name: '',
    domain: '',
    status: 'active',
    plan_type: 'basic',
  });
  const [newPhone, setNewPhone] = useState({
    phone_number: '',
    channel: 'voice',
    region: '',
  });

  useEffect(() => {
    fetchOrganisations();
  }, []);

  const fetchOrganisations = async () => {
    try {
      setLoading(true);
      const response = await organisationAPI.getAll();
      setOrganisations(response.data);
    } catch (error) {
      console.error('Error fetching organisations:', error);
      toast.error('Failed to fetch organisations');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrg = async (e) => {
    e.preventDefault();
    try {
      await organisationAPI.create(newOrg);
      toast.success('Organisation created successfully');
      setDialogOpen(false);
      setNewOrg({
        name: '',
        domain: '',
        status: 'active',
        plan_type: 'basic',
      });
      fetchOrganisations();
    } catch (error) {
      console.error('Error creating organisation:', error);
      toast.error(error.response?.data?.detail || 'Failed to create organisation');
    }
  };

  const handleAddPhone = async (e) => {
    e.preventDefault();
    try {
      await organisationAPI.addPhone(selectedOrg.id, newPhone);
      toast.success('Phone number added successfully');
      setPhoneDialogOpen(false);
      setNewPhone({ phone_number: '', channel: 'voice', region: '' });
      fetchOrganisations();
    } catch (error) {
      console.error('Error adding phone:', error);
      toast.error(error.response?.data?.detail || 'Failed to add phone number');
    }
  };

  const openPhoneDialog = (org) => {
    setSelectedOrg(org);
    setPhoneDialogOpen(true);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'inactive':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'suspended':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPlanColor = (plan) => {
    switch (plan) {
      case 'enterprise':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'professional':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'basic':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-4xl font-bold tracking-tight">Organisation Management</h2>
          <p className="text-muted-foreground mt-2 text-lg">Manage multi-tenant organisations</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="rounded-full font-medium shadow-sm hover:shadow-md transition-all">
              <Plus className="w-4 h-4 mr-2" />
              Add Organisation
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Organisation</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateOrg}>
              <div className="space-y-4 py-4">
                <div>
                  <Label htmlFor="name">Organisation Name</Label>
                  <Input
                    id="name"
                    value={newOrg.name}
                    onChange={(e) => setNewOrg({ ...newOrg, name: e.target.value })}
                    required
                    minLength={3}
                    placeholder="e.g., Bayer India"
                  />
                </div>
                <div>
                  <Label htmlFor="domain">Domain</Label>
                  <Input
                    id="domain"
                    value={newOrg.domain}
                    onChange={(e) => setNewOrg({ ...newOrg, domain: e.target.value })}
                    placeholder="e.g., bayer.kisanvani.ai"
                  />
                </div>
                <div>
                  <Label htmlFor="status">Status</Label>
                  <Select value={newOrg.status} onValueChange={(value) => setNewOrg({ ...newOrg, status: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                      <SelectItem value="suspended">Suspended</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="plan">Plan Type</Label>
                  <Select value={newOrg.plan_type} onValueChange={(value) => setNewOrg({ ...newOrg, plan_type: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select plan" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="basic">Basic</SelectItem>
                      <SelectItem value="professional">Professional</SelectItem>
                      <SelectItem value="enterprise">Enterprise</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">Create Organisation</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
      <div className="grid grid-cols-1 gap-4">
        {organisations.map((org) => (
          <Card key={org.id} className="p-6 border border-border/60 hover:border-primary/20 transition-all">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <Building2 className="w-6 h-6 text-primary" />
                  <h3 className="text-xl font-semibold">{org.name}</h3>
                  <Badge className={getStatusColor(org.status)}>
                    {org.status}
                  </Badge>
                  <Badge className={getPlanColor(org.plan_type)}>
                    {org.plan_type}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-2">
                  {org.domain || 'No domain assigned'}
                </p>
                <p className="text-xs text-muted-foreground">
                  Created: {new Date(org.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => openPhoneDialog(org)}
                  title="Add phone number"
                >
                  <PhoneIcon className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
      
      {/* Add Phone Dialog */}
      <Dialog open={phoneDialogOpen} onOpenChange={setPhoneDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Phone Number</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAddPhone}>
            <div className="space-y-4 py-4">
              <div>
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  value={newPhone.phone_number}
                  onChange={(e) => setNewPhone({ ...newPhone, phone_number: e.target.value })}
                  required
                  placeholder="+91 1800-XXX-XXX"
                />
              </div>
              <div>
                <Label htmlFor="channel">Channel</Label>
                <Select value={newPhone.channel} onValueChange={(value) => setNewPhone({ ...newPhone, channel: value })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select channel" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="voice">Voice</SelectItem>
                    <SelectItem value="whatsapp">WhatsApp</SelectItem>
                    <SelectItem value="sms">SMS</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="region">Region (Optional)</Label>
                <Input
                  id="region"
                  value={newPhone.region}
                  onChange={(e) => setNewPhone({ ...newPhone, region: e.target.value })}
                  placeholder="e.g., Maharashtra, Gujarat"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="submit">Add Phone Number</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
