import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tag, Plus, Edit2, Trash2, Search, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/api/api';

export default function CompanyBrands() {
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    logo_url: '',
    is_active: true
  });

  useEffect(() => {
    fetchBrands();
  }, []);

  const fetchBrands = async () => {
    setLoading(true);
    try {
      // Company can access organisation's brands
      const response = await api.get('/org-admin/brands');
      setBrands(response.data || []);
    } catch (error) {
      console.error('Error fetching brands:', error);
      if (error.response?.status === 403) {
        toast.error('Access denied. Please contact your organisation admin.');
      } else {
        toast.error(error.response?.data?.detail || 'Failed to load brands');
      }
      setBrands([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.name) {
      toast.error('Brand name is required');
      return;
    }

    setLoading(true);
    try {
      await api.post('/org-admin/brands', formData);
      toast.success('Brand created successfully');
      setShowCreateModal(false);
      resetForm();
      fetchBrands();
    } catch (error) {
      console.error('Error creating brand:', error);
      toast.error(error.response?.data?.detail || 'Failed to create brand');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async () => {
    if (!formData.name) {
      toast.error('Brand name is required');
      return;
    }

    setLoading(true);
    try {
      await api.put(`/org-admin/brands/${selectedBrand.id}`, formData);
      toast.success('Brand updated successfully');
      setShowEditModal(false);
      setSelectedBrand(null);
      resetForm();
      fetchBrands();
    } catch (error) {
      console.error('Error updating brand:', error);
      toast.error(error.response?.data?.detail || 'Failed to update brand');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (brand) => {
    if (!confirm(`Are you sure you want to delete "${brand.name}"?`)) {
      return;
    }

    setLoading(true);
    try {
      await api.delete(`/org-admin/brands/${brand.id}`);
      toast.success('Brand deleted successfully');
      fetchBrands();
    } catch (error) {
      console.error('Error deleting brand:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete brand');
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = () => {
    resetForm();
    setShowCreateModal(true);
  };

  const openEditModal = (brand) => {
    setSelectedBrand(brand);
    setFormData({
      name: brand.name || '',
      description: brand.description || '',
      logo_url: brand.logo_url || '',
      is_active: brand.is_active !== false
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      logo_url: '',
      is_active: true
    });
  };

  const filteredBrands = brands.filter(brand =>
    brand.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    brand.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Tag className="w-8 h-8 text-primary" />
            My Brands
          </h1>
          <p className="text-muted-foreground mt-1">Manage your company brands</p>
        </div>
        <Button onClick={openCreateModal} className="gap-2">
          <Plus className="w-4 h-4" />
          Add Brand
        </Button>
      </div>

      {/* Search */}
      <Card className="p-4">
        <div className="flex items-center gap-2">
          <Search className="w-5 h-5 text-muted-foreground" />
          <Input
            placeholder="Search brands..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1"
          />
        </div>
      </Card>

      {/* Brands List */}
      {loading ? (
        <div className="text-center py-8">Loading brands...</div>
      ) : filteredBrands.length === 0 ? (
        <Card className="p-8 text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-lg text-muted-foreground">
            {searchTerm ? 'No brands found matching your search' : 'No brands yet. Create your first brand!'}
          </p>
          {!searchTerm && (
            <Button onClick={openCreateModal} className="mt-4">
              <Plus className="w-4 h-4 mr-2" />
              Create Brand
            </Button>
          )}
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredBrands.map((brand) => (
            <Card key={brand.id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {brand.logo_url ? (
                    <img src={brand.logo_url} alt={brand.name} className="w-12 h-12 rounded-lg object-cover" />
                  ) : (
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Tag className="w-6 h-6 text-primary" />
                    </div>
                  )}
                  <div>
                    <h3 className="font-semibold text-lg">{brand.name}</h3>
                    <span className={`text-xs px-2 py-1 rounded ${brand.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                      {brand.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>
              
              {brand.description && (
                <p className="text-sm text-muted-foreground mb-4">{brand.description}</p>
              )}
              
              <div className="flex gap-2 pt-4 border-t">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => openEditModal(brand)}
                  className="flex-1"
                >
                  <Edit2 className="w-4 h-4 mr-2" />
                  Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDelete(brand)}
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create New Brand</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Brand Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Premium Seeds"
                required
              />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief description of the brand"
              />
            </div>
            <div>
              <Label htmlFor="logo_url">Logo URL</Label>
              <Input
                id="logo_url"
                value={formData.logo_url}
                onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                placeholder="https://example.com/logo.png"
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded"
              />
              <Label htmlFor="is_active">Active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={loading}>
              {loading ? 'Creating...' : 'Create Brand'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Brand</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="edit_name">Brand Name *</Label>
              <Input
                id="edit_name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
            <div>
              <Label htmlFor="edit_description">Description</Label>
              <Input
                id="edit_description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="edit_logo_url">Logo URL</Label>
              <Input
                id="edit_logo_url"
                value={formData.logo_url}
                onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="edit_is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded"
              />
              <Label htmlFor="edit_is_active">Active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditModal(false)}>Cancel</Button>
            <Button onClick={handleEdit} disabled={loading}>
              {loading ? 'Updating...' : 'Update Brand'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
