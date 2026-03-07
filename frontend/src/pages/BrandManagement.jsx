import React, { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, Tag, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import api, { brandAPI, organisationAPI } from '@/api/api';

export default function BrandManagement() {
  const [brands, setBrands] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [organisations, setOrganisations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingBrand, setEditingBrand] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    organisation_id: '',
    company_id: '',
    description: '',
    logo_url: '',
    is_active: true
  });

  useEffect(() => {
    fetchBrands();
    fetchCompanies();
    fetchOrganisations();
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

  const fetchOrganisations = async () => {
    try {
      const response = await organisationAPI.getAll(0, 500);
      setOrganisations(response.data || []);
    } catch (error) {
      console.error('Error fetching organisations:', error);
      toast.error('Failed to load organisations');
    }
  };

  const handleOpenDialog = (brand = null) => {
    if (brand) {
      setEditingBrand(brand);
      setFormData({
        name: brand.name || '',
        organisation_id: brand.organisation_id?.toString() || '',
        company_id: brand.company_id?.toString() || '',
        description: brand.description || '',
        logo_url: brand.logo_url || '',
        is_active: brand.is_active ?? true
      });
    } else {
      setEditingBrand(null);
      setFormData({
        name: '',
        organisation_id: '',
        company_id: '',
        description: '',
        logo_url: '',
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
      organisation_id: '',
      company_id: '',
      description: '',
      logo_url: '',
      is_active: true
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error('Brand name is required');
      return;
    }

    if (!formData.organisation_id) {
      toast.error('Please select an organisation');
      return;
    }

    if (!formData.company_id) {
      toast.error('Please select a company');
      return;
    }

    try {
      const payload = {
        name: formData.name.trim(),
        organisation_id: parseInt(formData.organisation_id),
        company_id: parseInt(formData.company_id),
        description: formData.description.trim() || null,
        logo_url: formData.logo_url.trim() || null,
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
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Tag className="h-8 w-8 text-primary" />
              Brand Management
            </h1>
            <Badge variant="secondary" className="mt-1 bg-purple-100 text-purple-700">{brands.length} Total Brands</Badge>
          </div>
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
                  <Label htmlFor="organisation_id">Organisation *</Label>
                  <Select
                    value={formData.organisation_id}
                    onValueChange={(value) => setFormData({ ...formData, organisation_id: value, company_id: '' })}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select organisation" />
                    </SelectTrigger>
                    <SelectContent>
                      {organisations.map((org) => (
                        <SelectItem key={org.id} value={org.id.toString()}>
                          {org.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="company_id">Company *</Label>
                  <Select
                    value={formData.company_id}
                    onValueChange={(value) => setFormData({ ...formData, company_id: value })}
                    required
                    disabled={!formData.organisation_id}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={formData.organisation_id ? "Select company" : "First select an organisation"} />
                    </SelectTrigger>
                    <SelectContent>
                      {companies
                        .filter(company => company.organisation_id?.toString() === formData.organisation_id)
                        .map((company) => (
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
                <div className="grid gap-2">
                  <Label htmlFor="logo_url">Logo URL</Label>
                  <Input
                    id="logo_url"
                    value={formData.logo_url}
                    onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                    placeholder="https://example.com/logo.png"
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
            <Card key={brand.id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {brand.logo_url ? (
                    <img
                      src={brand.logo_url}
                      alt={brand.name}
                      className="w-12 h-12 rounded-lg object-contain bg-gray-50 border"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Tag className="w-6 h-6 text-primary" />
                    </div>
                  )}
                  <div>
                    <h3 className="font-semibold text-lg leading-tight">{brand.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                        {getCompanyName(brand.company_id)}
                      </span>
                      <Badge variant={brand.is_active ? 'default' : 'secondary'} className="text-[10px] px-2 py-0 font-medium">
                        {brand.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>

              {brand.description && (
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2 min-h-[40px]">
                  {brand.description}
                </p>
              )}

              <div className="flex items-center justify-between pt-4 border-t">
                <div className="flex items-center gap-2">
                  {brand.product_count !== undefined && (
                    <Badge variant="outline" className="text-[10px] font-medium">
                      {brand.product_count} Products
                    </Badge>
                  )}
                  {brand.created_at && (
                    <span className="text-[10px] text-muted-foreground">
                      {new Date(brand.created_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => handleOpenDialog(brand)}
                  >
                    <Pencil className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/5"
                    onClick={() => handleDelete(brand.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
