import React, { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, Package, Search, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import api, { productAPI, brandAPI } from '@/api/api';

export default function ProductManagement() {
  const [products, setProducts] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [selectedBrandForUpload, setSelectedBrandForUpload] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    brand_id: '',
    description: '',
    category: '',
    target_crops: '',
    target_problems: '',
    application_method: '',
    dosage_info: '',
    is_active: true
  });

  useEffect(() => {
    fetchProducts();
    fetchBrands();
  }, []);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await productAPI.getAll();
      setProducts(response.data || []);
    } catch (error) {
      console.error('Error fetching products:', error);
      toast.error('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  const fetchBrands = async () => {
    try {
      const response = await brandAPI.getAll();
      setBrands(response.data || []);
    } catch (error) {
      console.error('Error fetching brands:', error);
      toast.error('Failed to load brands');
    }
  };

  const handleOpenDialog = (product = null) => {
    if (product) {
      setEditingProduct(product);
      setFormData({
        name: product.name || '',
        brand_id: product.brand_id?.toString() || '',
        description: product.description || '',
        category: product.category || '',
        target_crops: product.target_crops || '',
        target_problems: product.target_problems || '',
        application_method: product.application_method || '',
        dosage_info: product.dosage_info || '',
        is_active: product.is_active ?? true
      });
    } else {
      setEditingProduct(null);
      setFormData({
        name: '',
        brand_id: '',
        description: '',
        category: '',
        target_crops: '',
        target_problems: '',
        application_method: '',
        dosage_info: '',
        is_active: true
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingProduct(null);
    setFormData({
      name: '',
      brand_id: '',
      description: '',
      category: '',
      target_crops: '',
      target_problems: '',
      application_method: '',
      dosage_info: '',
      is_active: true
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast.error('Product name is required');
      return;
    }
    
    if (!formData.brand_id) {
      toast.error('Please select a brand');
      return;
    }

    try {
      const payload = {
        name: formData.name.trim(),
        brand_id: parseInt(formData.brand_id),
        description: formData.description.trim() || null,
        category: formData.category.trim() || null,
        target_crops: formData.target_crops.trim() || null,
        target_problems: formData.target_problems.trim() || null,
        application_method: formData.application_method.trim() || null,
        dosage_info: formData.dosage_info.trim() || null,
        is_active: formData.is_active
      };

      if (editingProduct) {
        await productAPI.update(editingProduct.id, payload);
        toast.success('Product updated successfully');
      } else {
        await productAPI.create(payload);
        toast.success('Product created successfully');
      }
      
      handleCloseDialog();
      fetchProducts();
    } catch (error) {
      console.error('Error saving product:', error);
      // Handle validation errors (Pydantic returns array of error objects)
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Failed to save product';
      
      if (Array.isArray(errorDetail)) {
        // Pydantic validation errors
        errorMessage = errorDetail.map(err => err.msg || JSON.stringify(err)).join(', ');
      } else if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      }
      
      toast.error(errorMessage);
    }
  };

  const handleDelete = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) {
      return;
    }

    try {
      await productAPI.delete(productId);
      toast.success('Product deleted successfully');
      fetchProducts();
    } catch (error) {
      console.error('Error deleting product:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete product');
    }
  };

  const getBrandName = (brandId) => {
    const brand = brands.find(b => b.id === brandId);
    return brand?.name || 'Unknown Brand';
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Check file type
      const validTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
      if (!validTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
        toast.error('Please upload a CSV or Excel file');
        return;
      }
      setCsvFile(file);
    }
  };

  const handleCsvUpload = async () => {
    if (!csvFile) {
      toast.error('Please select a file to upload');
      return;
    }
    
    if (!selectedBrandForUpload) {
      toast.error('Please select a brand');
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', csvFile);
      formData.append('brand_id', selectedBrandForUpload);

      const response = await api.post('/products/upload-csv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success(`Successfully uploaded ${response.data.success_count} products!`);
      setUploadDialogOpen(false);
      setCsvFile(null);
      setSelectedBrandForUpload('');
      fetchProducts();
    } catch (error) {
      console.error('Error uploading CSV:', error);
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Failed to upload CSV';
      
      if (Array.isArray(errorDetail)) {
        errorMessage = errorDetail.map(err => err.msg || JSON.stringify(err)).join(', ');
      } else if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      }
      
      toast.error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const filteredProducts = products.filter(product => 
    product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.category?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.target_crops?.toLowerCase().includes(searchQuery.toLowerCase())
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
          <h1 className="text-3xl font-bold tracking-tight">Product Management</h1>
          <p className="text-muted-foreground mt-1">
            Manage agricultural products and solutions
          </p>
        </div>
        <div className="flex gap-2">
          {/* CSV Upload Dialog */}
          <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Upload className="w-4 h-4 mr-2" />
                Upload CSV
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Upload Products CSV</DialogTitle>
                <DialogDescription>
                  Select a brand and upload CSV file. All products in the file will be added to the selected brand.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="upload-brand">Select Brand *</Label>
                  <Select
                    value={selectedBrandForUpload}
                    onValueChange={(value) => setSelectedBrandForUpload(value)}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select brand for products" />
                    </SelectTrigger>
                    <SelectContent>
                      {brands.map((brand) => (
                        <SelectItem key={brand.id} value={brand.id.toString()}>
                          {brand.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="csv-file">Select File</Label>
                  <Input
                    id="csv-file"
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileChange}
                  />
                  {csvFile && (
                    <p className="text-sm text-muted-foreground">
                      Selected: {csvFile.name}
                    </p>
                  )}
                </div>
                <div className="rounded-md bg-blue-50 p-4 text-sm text-blue-800">
                  <p className="font-medium mb-1">CSV Format:</p>
                  <p>name, category, description, target_crops, target_problems, dosage, usage_instructions</p>
                  <p className="text-xs mt-2">Note: brand_id is not needed in CSV - all products will use the selected brand above</p>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => {
                  setUploadDialogOpen(false);
                  setCsvFile(null);
                  setSelectedBrandForUpload('');
                }}>
                  Cancel
                </Button>
                <Button 
                  type="button" 
                  onClick={handleCsvUpload}
                  disabled={!csvFile || uploading}
                >
                  {uploading ? 'Uploading...' : 'Upload'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* Add Product Dialog */}
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button onClick={() => handleOpenDialog()}>
                <Plus className="w-4 h-4 mr-2" />
                Add Product
              </Button>
            </DialogTrigger>
          <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
            <form onSubmit={handleSubmit}>
              <DialogHeader>
                <DialogTitle>
                  {editingProduct ? 'Edit Product' : 'Create New Product'}
                </DialogTitle>
                <DialogDescription>
                  {editingProduct 
                    ? 'Update the product information below.' 
                    : 'Add a new product to a brand.'}
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="brand_id">Brand *</Label>
                  <Select
                    value={formData.brand_id}
                    onValueChange={(value) => setFormData({ ...formData, brand_id: value })}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select brand" />
                    </SelectTrigger>
                    <SelectContent>
                      {brands.map((brand) => (
                        <SelectItem key={brand.id} value={brand.id.toString()}>
                          {brand.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="name">Product Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Confidor Super"
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="category">Category</Label>
                  <Input
                    id="category"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="e.g., Insecticide, Fungicide, Herbicide"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Detailed product description"
                    rows={3}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="target_crops">Target Crops</Label>
                  <Input
                    id="target_crops"
                    value={formData.target_crops}
                    onChange={(e) => setFormData({ ...formData, target_crops: e.target.value })}
                    placeholder="e.g., Cotton, Tomato, Wheat (comma separated)"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="target_problems">Target Problems</Label>
                  <Input
                    id="target_problems"
                    value={formData.target_problems}
                    onChange={(e) => setFormData({ ...formData, target_problems: e.target.value })}
                    placeholder="e.g., Aphids, Whitefly, Leaf curl (comma separated)"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="application_method">Application Method</Label>
                  <Input
                    id="application_method"
                    value={formData.application_method}
                    onChange={(e) => setFormData({ ...formData, application_method: e.target.value })}
                    placeholder="e.g., Foliar spray, Soil drench"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="dosage_info">Dosage Information</Label>
                  <Textarea
                    id="dosage_info"
                    value={formData.dosage_info}
                    onChange={(e) => setFormData({ ...formData, dosage_info: e.target.value })}
                    placeholder="Recommended dosage and application details"
                    rows={2}
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
                    Active Product
                  </Label>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={handleCloseDialog}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editingProduct ? 'Update Product' : 'Create Product'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search products by name, category, or crops..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredProducts.length === 0 ? (
          <Card className="col-span-full">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Package className="w-12 h-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium">
                {searchQuery ? 'No products found' : 'No products available'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {searchQuery ? 'Try adjusting your search' : 'Create your first product to get started'}
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredProducts.map((product) => (
            <Card key={product.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-xl">{product.name}</CardTitle>
                    <CardDescription className="mt-1">
                      {getBrandName(product.brand_id)}
                    </CardDescription>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleOpenDialog(product)}
                    >
                      <Pencil className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(product.id)}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {product.category && (
                    <div>
                      <Badge variant="outline">{product.category}</Badge>
                    </div>
                  )}
                  {product.description && (
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {product.description}
                    </p>
                  )}
                  {product.target_crops && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">Target Crops:</p>
                      <p className="text-sm">{product.target_crops}</p>
                    </div>
                  )}
                  {product.target_problems && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">Treats:</p>
                      <p className="text-sm">{product.target_problems}</p>
                    </div>
                  )}
                  <div className="flex items-center gap-2 pt-2">
                    <Badge variant={product.is_active ? 'default' : 'secondary'}>
                      {product.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
