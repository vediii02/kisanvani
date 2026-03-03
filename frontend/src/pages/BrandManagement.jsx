import React, { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, Package, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import api, { brandAPI } from '@/api/api';

export default function BrandManagement() {
  const [brands, setBrands] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingBrand, setEditingBrand] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    company_id: '',
    description: '',
    is_active: true
  });

  useEffect(() => {
    fetchBrands();
    fetchCompanies();
  }, []);

  const fetchBrands = async () => {
    try {
      setLoading(true);
      const response = await brandAPI.getAll();
      setBrands(response.data || []);
    } catch (error) {
      console.error('Error fetching brands:', error);
      toast.error('Failed to load brands');
    } finally {
      setLoading(false);
    }
  };

  const fetchCompanies = async () => {
    try {
      const response = await api.get('/admin/companies');
      setCompanies(response.data || []);
    } catch (error) {
      console.error('Error fetching companies:', error);
      toast.error('Failed to load companies');
    }
  };

  const handleOpenDialog = (brand = null) => {
    if (brand) {
      setEditingBrand(brand);
      setFormData({
        name: brand.name || '',
        company_id: brand.company_id?.toString() || '',
        description: brand.description || '',
        is_active: brand.is_active ?? true
      });
    } else {
      setEditingBrand(null);
      setFormData({
        name: '',
        company_id: '',
        description: '',
        is_active: true
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingBrand(null);
    setFormData({
      name: '',
      company_id: '',
      description: '',
      is_active: true
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error('Brand name is required');
      return;
    }

    if (!formData.company_id) {
      toast.error('Please select a company');
      return;
    }

    try {
      // Get the selected company's organisation_id
      const selectedCompany = companies.find(c => c.id === parseInt(formData.company_id));
      if (!selectedCompany) {
        toast.error('Selected company not found');
        return;
      }

      const payload = {
        name: formData.name.trim(),
        organisation_id: selectedCompany.organisation_id,
        company_id: parseInt(formData.company_id),
        description: formData.description.trim() || null,
        is_active: formData.is_active
      };

      if (editingBrand) {
        await brandAPI.update(editingBrand.id, payload);
        toast.success('Brand updated successfully');
      } else {
        await brandAPI.create(payload);
        toast.success('Brand created successfully');
      }

      handleCloseDialog();
      fetchBrands();
    } catch (error) {
      console.error('Error saving brand:', error);
      // Handle validation errors (Pydantic returns array of error objects)
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Failed to save brand';

      if (Array.isArray(errorDetail)) {
        // Pydantic validation errors
        errorMessage = errorDetail.map(err => {
          if (typeof err === 'string') return err;
          if (err.msg) return String(err.msg);
          if (err.loc && err.msg) return `${Array.isArray(err.loc) ? err.loc.join('.') : String(err.loc)}: ${String(err.msg)}`;
          return 'Validation error';
        }).join(', ');
      } else if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      }

      toast.error(errorMessage);
    }
  };

  const handleDelete = async (brandId) => {
    if (!window.confirm('Are you sure you want to delete this brand? This will also delete all associated products.')) {
      return;
    }

    try {
      await brandAPI.delete(brandId);
      toast.success('Brand deleted successfully');
      fetchBrands();
    } catch (error) {
      console.error('Error deleting brand:', error);
      toast.error(getErrorMessage(error));
    }
  };

  const getCompanyName = (companyId) => {
    const company = companies.find(c => c.id === companyId);
    return company?.name || 'No company assigned';
  };

  const filteredBrands = brands.filter(brand =>
    brand.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    brand.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    getCompanyName(brand.company_id).toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Brand Management</h1>
          <p className="text-muted-foreground mt-1">
            Manage brands across all organisations
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => handleOpenDialog()}>
              <Plus className="w-4 h-4 mr-2" />
              Add Brand
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <form onSubmit={handleSubmit}>
              <DialogHeader>
                <DialogTitle>
                  {editingBrand ? 'Edit Brand' : 'Create New Brand'}
                </DialogTitle>
                <DialogDescription>
                  {editingBrand
                    ? 'Update the brand information below.'
                    : 'Add a new brand to a company.'}
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="company_id">Company *</Label>
                  <Select
                    value={formData.company_id}
                    onValueChange={(value) => setFormData({ ...formData, company_id: value })}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select company" />
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
                <div className="grid gap-2">
                  <Label htmlFor="name">Brand Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Bayer CropScience"
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Brief description of the brand"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <Label htmlFor="is_active" className="cursor-pointer">
                    Active Brand
                  </Label>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={handleCloseDialog}>
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

      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search brands by name, description, or company..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredBrands.length === 0 ? (
          <Card className="col-span-full">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Package className="w-12 h-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium">
                {searchQuery ? 'No brands found' : 'No brands available'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {searchQuery ? 'Try adjusting your search' : 'Create your first brand to get started'}
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredBrands.map((brand) => (
            <Card key={brand.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-xl">{brand.name}</CardTitle>
                    <CardDescription className="mt-1">
                      {getCompanyName(brand.company_id)}
                    </CardDescription>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleOpenDialog(brand)}
                    >
                      <Pencil className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(brand.id)}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {brand.description && (
                  <p className="text-sm text-muted-foreground mb-3">
                    {brand.description}
                  </p>
                )}
                <div className="flex items-center gap-2">
                  <Badge variant={brand.is_active ? 'default' : 'secondary'}>
                    {brand.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  {brand.product_count !== undefined && (
                    <Badge variant="outline">
                      {brand.product_count} Products
                    </Badge>
                  )}
                </div>
                {brand.created_at && (
                  <p className="text-xs text-muted-foreground mt-3">
                    Created: {new Date(brand.created_at).toLocaleDateString()}
                  </p>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
