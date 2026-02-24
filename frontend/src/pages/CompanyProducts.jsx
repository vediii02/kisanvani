import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Package, Plus, Edit2, Trash2, Search, Upload, Download, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/api/api';

export default function CompanyProducts() {
  const [products, setProducts] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [selectedBrandForUpload, setSelectedBrandForUpload] = useState('');
  const [formData, setFormData] = useState({
    brand_id: '',
    name: '',
    category: '',
    sub_category: '',
    description: '',
    target_crops: '',
    target_problems: '',
    dosage: '',
    usage_instructions: '',
    safety_precautions: '',
    price_range: '',
    is_active: true
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Company can access organisation's brands and products
      const [productsRes, brandsRes] = await Promise.all([
        api.get('/org-admin/products'),
        api.get('/org-admin/brands')
      ]);
      setProducts(productsRes.data || []);
      setBrands(brandsRes.data || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      if (error.response?.status === 403) {
        toast.error('Access denied. Please contact your organisation admin.');
      } else {
        toast.error(error.response?.data?.detail || 'Failed to load data');
      }
      setProducts([]);
      setBrands([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.brand_id) {
      toast.error('Product name and brand are required');
      return;
    }

    setLoading(true);
    try {
      await api.post('/org-admin/products', formData);
      toast.success('Product created successfully');
      setShowCreateModal(false);
      resetForm();
      fetchData();
    } catch (error) {
      console.error('Error creating product:', error);
      toast.error(error.response?.data?.detail || 'Failed to create product');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async () => {
    if (!formData.name || !formData.brand_id) {
      toast.error('Product name and brand are required');
      return;
    }

    setLoading(true);
    try {
      await api.put(`/org-admin/products/${selectedProduct.id}`, formData);
      toast.success('Product updated successfully');
      setShowEditModal(false);
      setSelectedProduct(null);
      resetForm();
      fetchData();
    } catch (error) {
      console.error('Error updating product:', error);
      toast.error(error.response?.data?.detail || 'Failed to update product');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (product) => {
    if (!confirm(`Are you sure you want to delete "${product.name}"?`)) {
      return;
    }

    setLoading(true);
    try {
      await api.delete(`/org-admin/products/${product.id}`);
      toast.success('Product deleted successfully');
      fetchData();
    } catch (error) {
      console.error('Error deleting product:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete product');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!uploadFile) {
      toast.error('Please select a file');
      return;
    }

    if (!selectedBrandForUpload) {
      toast.error('Please select a brand for the products');
      return;
    }

    console.log('Upload file:', uploadFile.name);
    console.log('Selected brand ID:', selectedBrandForUpload);

    const formDataUpload = new FormData();
    formDataUpload.append('file', uploadFile);
    formDataUpload.append('brand_id', selectedBrandForUpload);

    setUploading(true);
    setUploadResult(null);
    
    try {
      console.log('Sending upload request...');
      const response = await api.post('/org-admin/products/upload-csv', formDataUpload, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      console.log('Upload response:', response.data);
      setUploadResult(response.data);
      
      // Show appropriate message based on results
      if (response.data.success_count > 0) {
        toast.success(`Successfully uploaded ${response.data.success_count} products`);
      } else if (response.data.error_count > 0) {
        toast.error(`Upload failed: ${response.data.errors[0] || 'No products were added'}`);
      } else {
        toast.warning('No products were uploaded. Please check your CSV file.');
      }
      
      // Refresh the products list if any were added
      if (response.data.success_count > 0) {
        await fetchData();
        
        // Close modal after successful upload
        setTimeout(() => {
          setShowUploadModal(false);
          setUploadFile(null);
          setUploadResult(null);
          setSelectedBrandForUpload('');
        }, 3000); // Give user 3 seconds to see the results
      }
      
    } catch (error) {
      console.error('Error uploading file:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload file');
      setUploadResult({
        success_count: 0,
        error_count: 1,
        errors: [error.response?.data?.detail || 'Upload failed']
      });
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => {
    const csvContent = `name,category,sub_category,description,target_crops,target_problems,dosage,usage_instructions,safety_precautions,price_range,is_active
Wheat Seed 101,Seeds,Wheat,High quality wheat seeds,Wheat,Low yield,10kg per acre,Sow in October-November,Wear gloves,Rs 500-600 per kg,true
Rice Seed XYZ,Seeds,Rice,Premium rice variety,Rice,Disease,8kg per acre,Sow in June-July,Store in dry place,Rs 400-500 per kg,true`;
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', 'products_template.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    toast.success('Template downloaded');
  };

  const openCreateModal = () => {
    resetForm();
    setShowCreateModal(true);
  };

  const openEditModal = (product) => {
    setSelectedProduct(product);
    setFormData({
      brand_id: product.brand_id || '',
      name: product.name || '',
      category: product.category || '',
      sub_category: product.sub_category || '',
      description: product.description || '',
      target_crops: product.target_crops || '',
      target_problems: product.target_problems || '',
      dosage: product.dosage || '',
      usage_instructions: product.usage_instructions || '',
      safety_precautions: product.safety_precautions || '',
      price_range: product.price_range || '',
      is_active: product.is_active !== false
    });
    setShowEditModal(true);
  };

  const openUploadModal = () => {
    setUploadFile(null);
    setUploadResult(null);
    setShowUploadModal(true);
  };

  const resetForm = () => {
    setFormData({
      brand_id: '',
      name: '',
      category: '',
      sub_category: '',
      description: '',
      target_crops: '',
      target_problems: '',
      dosage: '',
      usage_instructions: '',
      safety_precautions: '',
      price_range: '',
      is_active: true
    });
  };

  const filteredProducts = products.filter(product =>
    product.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.category?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getBrandName = (brandId) => {
    const brand = brands.find(b => b.id === brandId);
    return brand?.name || 'Unknown Brand';
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Package className="w-8 h-8 text-primary" />
            My Products
          </h1>
          <p className="text-muted-foreground mt-1">Manage your company products</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={openUploadModal} variant="outline" className="gap-2">
            <Upload className="w-4 h-4" />
            Upload CSV
          </Button>
          <Button onClick={openCreateModal} className="gap-2">
            <Plus className="w-4 h-4" />
            Add Product
          </Button>
        </div>
      </div>

      {/* Search */}
      <Card className="p-4">
        <div className="flex items-center gap-2">
          <Search className="w-5 h-5 text-muted-foreground" />
          <Input
            placeholder="Search products by name, category, or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1"
          />
        </div>
      </Card>

      {/* Products List */}
      {loading ? (
        <div className="text-center py-8">Loading products...</div>
      ) : filteredProducts.length === 0 ? (
        <Card className="p-8 text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-lg text-muted-foreground mb-2">
            {searchTerm ? 'No products found matching your search' : 'No products yet.'}
          </p>
          <p className="text-sm text-muted-foreground mb-4">
            Start by adding products manually or upload via CSV
          </p>
          <div className="flex gap-2 justify-center">
            <Button onClick={openUploadModal} variant="outline">
              <Upload className="w-4 h-4 mr-2" />
              Upload CSV
            </Button>
            <Button onClick={openCreateModal}>
              <Plus className="w-4 h-4 mr-2" />
              Add Product
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProducts.map((product) => (
            <Card key={product.id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg mb-1">{product.name}</h3>
                  <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700">
                    {getBrandName(product.brand_id)}
                  </span>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${product.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                  {product.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              {product.category && (
                <p className="text-sm text-muted-foreground mb-2">
                  <strong>Category:</strong> {product.category}
                  {product.sub_category && ` > ${product.sub_category}`}
                </p>
              )}
              
              {product.description && (
                <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{product.description}</p>
              )}
              
              {product.target_crops && (
                <p className="text-xs text-muted-foreground mb-2">
                  <strong>Target Crops:</strong> {product.target_crops}
                </p>
              )}
              
              {product.price_range && (
                <p className="text-sm font-semibold text-primary mb-3">{product.price_range}</p>
              )}
              
              <div className="flex gap-2 pt-3 border-t">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => openEditModal(product)}
                  className="flex-1"
                >
                  <Edit2 className="w-4 h-4 mr-2" />
                  Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDelete(product)}
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
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Add New Product</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Product Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Wheat Seed Premium"
                  required
                />
              </div>
              <div>
                <Label htmlFor="brand_id">Brand *</Label>
                {brands.length === 0 ? (
                  <div className="border rounded-md p-3 bg-yellow-50 border-yellow-200">
                    <p className="text-sm text-yellow-800 mb-2">
                      ⚠️ No brands available. Please create a brand first.
                    </p>
                    <a 
                      href="/company/brands" 
                      className="text-sm text-blue-600 hover:underline"
                    >
                      Go to Brands →
                    </a>
                  </div>
                ) : (
                  <Select value={formData.brand_id?.toString()} onValueChange={(value) => setFormData({ ...formData, brand_id: parseInt(value) })}>
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
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="category">Category</Label>
                <Input
                  id="category"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  placeholder="e.g., Seeds, Pesticides"
                />
              </div>
              <div>
                <Label htmlFor="sub_category">Sub Category</Label>
                <Input
                  id="sub_category"
                  value={formData.sub_category}
                  onChange={(e) => setFormData({ ...formData, sub_category: e.target.value })}
                  placeholder="e.g., Wheat, Rice"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Product description"
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="target_crops">Target Crops</Label>
                <Input
                  id="target_crops"
                  value={formData.target_crops}
                  onChange={(e) => setFormData({ ...formData, target_crops: e.target.value })}
                  placeholder="e.g., Wheat, Rice, Cotton"
                />
              </div>
              <div>
                <Label htmlFor="target_problems">Target Problems</Label>
                <Input
                  id="target_problems"
                  value={formData.target_problems}
                  onChange={(e) => setFormData({ ...formData, target_problems: e.target.value })}
                  placeholder="e.g., Disease, Pest control"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="dosage">Dosage</Label>
                <Input
                  id="dosage"
                  value={formData.dosage}
                  onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                  placeholder="e.g., 10kg per acre"
                />
              </div>
              <div>
                <Label htmlFor="price_range">Price Range</Label>
                <Input
                  id="price_range"
                  value={formData.price_range}
                  onChange={(e) => setFormData({ ...formData, price_range: e.target.value })}
                  placeholder="e.g., Rs 500-600 per kg"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="usage_instructions">Usage Instructions</Label>
              <Textarea
                id="usage_instructions"
                value={formData.usage_instructions}
                onChange={(e) => setFormData({ ...formData, usage_instructions: e.target.value })}
                placeholder="How to use this product"
                rows={2}
              />
            </div>

            <div>
              <Label htmlFor="safety_precautions">Safety Precautions</Label>
              <Textarea
                id="safety_precautions"
                value={formData.safety_precautions}
                onChange={(e) => setFormData({ ...formData, safety_precautions: e.target.value })}
                placeholder="Safety guidelines"
                rows={2}
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
              {loading ? 'Creating...' : 'Create Product'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Product</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_name">Product Name *</Label>
                <Input
                  id="edit_name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label htmlFor="edit_brand_id">Brand *</Label>
                <Select value={formData.brand_id?.toString()} onValueChange={(value) => setFormData({ ...formData, brand_id: parseInt(value) })}>
                  <SelectTrigger>
                    <SelectValue />
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
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_category">Category</Label>
                <Input
                  id="edit_category"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit_sub_category">Sub Category</Label>
                <Input
                  id="edit_sub_category"
                  value={formData.sub_category}
                  onChange={(e) => setFormData({ ...formData, sub_category: e.target.value })}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="edit_description">Description</Label>
              <Textarea
                id="edit_description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_target_crops">Target Crops</Label>
                <Input
                  id="edit_target_crops"
                  value={formData.target_crops}
                  onChange={(e) => setFormData({ ...formData, target_crops: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit_target_problems">Target Problems</Label>
                <Input
                  id="edit_target_problems"
                  value={formData.target_problems}
                  onChange={(e) => setFormData({ ...formData, target_problems: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_dosage">Dosage</Label>
                <Input
                  id="edit_dosage"
                  value={formData.dosage}
                  onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit_price_range">Price Range</Label>
                <Input
                  id="edit_price_range"
                  value={formData.price_range}
                  onChange={(e) => setFormData({ ...formData, price_range: e.target.value })}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="edit_usage_instructions">Usage Instructions</Label>
              <Textarea
                id="edit_usage_instructions"
                value={formData.usage_instructions}
                onChange={(e) => setFormData({ ...formData, usage_instructions: e.target.value })}
                rows={2}
              />
            </div>

            <div>
              <Label htmlFor="edit_safety_precautions">Safety Precautions</Label>
              <Textarea
                id="edit_safety_precautions"
                value={formData.safety_precautions}
                onChange={(e) => setFormData({ ...formData, safety_precautions: e.target.value })}
                rows={2}
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
              {loading ? 'Updating...' : 'Update Product'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* CSV Upload Modal */}
      <Dialog open={showUploadModal} onOpenChange={setShowUploadModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Upload Products via CSV</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {brands.length === 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="font-semibold text-yellow-900 mb-1">No Brands Available</h4>
                    <p className="text-sm text-yellow-700 mb-2">
                      You need to create at least one brand before uploading products. 
                      Products must be associated with a brand.
                    </p>
                    <a 
                      href="/company/brands" 
                      className="text-sm text-blue-600 hover:underline font-medium"
                    >
                      Create Brands First →
                    </a>
                  </div>
                </div>
              </div>
            )}
            
            {/* <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <FileText className="w-5 h-5 text-blue-600 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-blue-900 mb-1">CSV Format Required</h4>
                  <p className="text-sm text-blue-700 mb-2">
                    Download the template to see the required format
                  </p>
                  <Button onClick={downloadTemplate} variant="outline" size="sm" className="gap-2">
                    <Download className="w-4 h-4" />
                    Download Template
                  </Button>
                </div>
              </div>
            </div> */}

            <div>
              <Label htmlFor="upload_brand">Select Brand *</Label>
              <Select value={selectedBrandForUpload} onValueChange={setSelectedBrandForUpload}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose brand for all products in CSV" />
                </SelectTrigger>
                <SelectContent>
                  {brands.map((brand) => (
                    <SelectItem key={brand.id} value={brand.id.toString()}>
                      {brand.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">
                All products in the CSV will be associated with this brand
              </p>
            </div>

            <div>
              <Label htmlFor="csv_file">Select CSV File</Label>
              <Input
                id="csv_file"
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className="cursor-pointer"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Supported formats: CSV, Excel (.xlsx, .xls)
              </p>
            </div>

            {uploadResult && (
              <div className={`border rounded-lg p-4 ${uploadResult.error_count > 0 ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'}`}>
                <div className="flex items-start gap-2">
                  {uploadResult.error_count > 0 ? (
                    <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                  ) : (
                    <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <h4 className="font-semibold mb-1">Upload Results</h4>
                    <p className="text-sm">✅ Successfully added: {uploadResult.success_count || 0} products</p>
                    {uploadResult.error_count > 0 && (
                      <p className="text-sm">❌ Failed: {uploadResult.error_count} products</p>
                    )}
                    {uploadResult.errors && uploadResult.errors.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs font-semibold mb-1">Errors:</p>
                        <ul className="text-xs space-y-1">
                          {uploadResult.errors.slice(0, 5).map((error, index) => (
                            <li key={index} className="text-red-600">• {error}</li>
                          ))}
                          {uploadResult.errors.length > 5 && (
                            <li className="text-muted-foreground">... and {uploadResult.errors.length - 5} more</li>
                          )}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUploadModal(false)}>Cancel</Button>
            <Button 
              onClick={handleFileUpload} 
              disabled={!uploadFile || !selectedBrandForUpload || uploading || brands.length === 0}
            >
              {uploading ? 'Uploading...' : brands.length === 0 ? 'Create Brands First' : 'Upload'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
