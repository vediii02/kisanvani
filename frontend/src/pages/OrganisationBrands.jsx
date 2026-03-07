// Organisation Brands Management
import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tag, Plus, Edit2, Trash2, Search, AlertCircle, Check, X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import api from '../api/api';

const OrganisationBrands = () => {
  const [brands, setBrands] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingBrand, setEditingBrand] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    logo_url: '',
    company_id: '',
    is_active: true
  });

  useEffect(() => {
    fetchBrands();
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await api.get('/organisation/companies');
      setCompanies(response.data.companies || []);
    } catch (err) {
      console.error('Failed to load companies:', err);
    }
  };

  const fetchBrands = async () => {
    try {
      setLoading(true);
      const response = await api.get('/brands');
      setBrands(response.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load brands');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.company_id) {
      toast.error('Brand name and company are required');
      return;
    }

    try {
      const payload = {
        ...formData,
        company_id: parseInt(formData.company_id)
      };

      if (editingBrand) {
        await api.put(`/brands/${editingBrand.id}`, payload);
        toast.success('Brand updated successfully');
      } else {
        await api.post('/brands', payload);
        toast.success('Brand created successfully');
      }
      setShowModal(false);
      resetForm();
      fetchBrands();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save brand');
    }
  };

  const resetForm = () => {
    setEditingBrand(null);
    setFormData({ name: '', description: '', logo_url: '', company_id: '', is_active: true });
  };

  const handleEdit = (brand) => {
    setEditingBrand(brand);
    setFormData({
      name: brand.name,
      description: brand.description || '',
      logo_url: brand.logo_url || '',
      company_id: brand.company_id?.toString() || '',
      is_active: brand.is_active
    });
    setShowModal(true);
  };

  const handleDelete = async (brand) => {
    if (!window.confirm(`Are you sure you want to delete "${brand.name}"?`)) return;

    try {
      await api.delete(`/brands/${brand.id}`);
      toast.success('Brand deleted successfully');
      fetchBrands();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete brand');
    }
  };

  const filteredBrands = brands.filter(brand =>
    brand.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    brand.company_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Tag className="w-8 h-8 text-primary" />
            Brands Management
          </h1>
          <Badge variant="secondary" className="mt-1 bg-purple-100 text-purple-700">{brands.length} Total Brands</Badge>
        </div>
        <Button onClick={() => { resetForm(); setShowModal(true); }} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Brand
        </Button>
      </div>

      {/* Search Bar */}
      <Card className="p-4">
        <div className="flex items-center gap-2">
          <Search className="h-5 w-5 text-muted-foreground" />
          <Input
            placeholder="Search brands or companies..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1"
          />
        </div>
      </Card>

      {/* Brands Grid */}
      {loading ? (
        <div className="flex justify-center py-12 text-muted-foreground">
          Loading brands...
        </div>
      ) : filteredBrands.length === 0 ? (
        <Card className="p-12 text-center">
          <Tag className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-900 mb-2">No Brands Found</h3>
          <p className="text-muted-foreground mb-6">
            {searchTerm ? 'Try a different search term' : 'Get started by creating your first brand'}
          </p>
          {!searchTerm && (
            <Button onClick={() => setShowModal(true)}>
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
                    <img src={brand.logo_url} alt={brand.name} className="w-12 h-12 rounded-lg object-contain bg-gray-50 border" />
                  ) : (
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Tag className="w-6 h-6 text-primary" />
                    </div>
                  )}
                  <div>
                    <h3 className="font-semibold text-lg leading-tight">{brand.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                        {brand.company_name}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${brand.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                        {brand.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {brand.description && (
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2 min-h-[40px]">{brand.description}</p>
              )}

              <div className="flex gap-2 pt-4 border-t">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleEdit(brand)}
                  className="flex-1"
                >
                  <Edit2 className="h-4 w-4 mr-2" />
                  Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDelete(brand)}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add/Edit Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingBrand ? 'Edit Brand' : 'Add New Brand'}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Brand Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g. Mahyco Seeds"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="company">Company Associate *</Label>
              <Select
                value={formData.company_id}
                onValueChange={(value) => setFormData({ ...formData, company_id: value })}
                required
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a company" />
                </SelectTrigger>
                <SelectContent>
                  {companies.map((company) => (
                    <SelectItem key={company.id} value={company.id.toString()}>
                      {company.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief description of the brand"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="logo">Logo URL</Label>
              <Input
                id="logo"
                type="url"
                value={formData.logo_url}
                onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                placeholder="https://example.com/logo.png"
              />
            </div>

            <div className="flex items-center space-x-2 py-2">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"
              />
              <Label htmlFor="is_active" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Active Brand
              </Label>
            </div>

            <DialogFooter className="pt-4">
              <Button type="button" variant="outline" onClick={() => setShowModal(false)}>
                Cancel
              </Button>
              <Button type="submit">
                {editingBrand ? 'Update Brand' : 'Create Brand'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default OrganisationBrands;
