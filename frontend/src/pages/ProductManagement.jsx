import React, { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, Package, Search, Upload, Download, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import api, { productAPI, brandAPI, organisationAPI } from '@/api/api';

// Category and Sub-category mapping
const CATEGORY_OPTIONS = {
  Pesticide: [
    "Insecticide",
    "Fungicide",
    "Herbicide",
    "Nematicide",
    "Acaricide",
    "Molluscicide",
  ],
  Fertilizer: [
    "NPK",
    "Organic",
    "Micronutrient",
    "Liquid Fertilizer",
    "Foliar Spray",
    "Biofertilizer",
  ],
  Seed: [
    "Hybrid",
    "Open Pollinated",
    "GMO",
    "Certified Seed",
    "Indigenous Variety",
  ],
  Equipment: [
    "Sprayer",
    "Drip Irrigation",
    "Mulcher",
    "Harvester",
    "Seeder",
    "Others",
  ],
  "Growth Regulator": [
    "Plant Hormone",
    "Nutrient Booster",
    "Root Promoter",
    "Stress Relief",
    "Yield Enhancer",
  ],
  Bioproduct: [
    "Bioinsecticide",
    "Biofungicide",
    "Bio-Nematicide",
    "Biofertilizer",
    "Bio-Stimulant",
  ],
  Other: ["General", "Miscellaneous"],
};

export default function ProductManagement() {
  const [products, setProducts] = useState([]);
  const [brands, setBrands] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [organisations, setOrganisations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadOrgId, setUploadOrgId] = useState('');
  const [uploadCompanyId, setUploadCompanyId] = useState('');
  const [selectedBrandForUpload, setSelectedBrandForUpload] = useState('');
  const [uploadResult, setUploadResult] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    organisation_id: '',
    company_id: '',
    brand_id: '',
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
    fetchProducts();
    fetchBrands();
    fetchCompanies();
    fetchOrganisations();
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
    }
  };

  const fetchCompanies = async () => {
    try {
      const response = await api.get('/admin/companies');
      setCompanies(response.data || []);
    } catch (error) {
      console.error('Error fetching companies:', error);
    }
  };

  const fetchOrganisations = async () => {
    try {
      const response = await organisationAPI.getAll(0, 500);
      setOrganisations(response.data || []);
    } catch (error) {
      console.error('Error fetching organisations:', error);
    }
  };

  const handleOpenDialog = (product = null) => {
    if (product) {
      setEditingProduct(product);
      setFormData({
        name: product.name || '',
        organisation_id: product.organisation_id?.toString() || '',
        company_id: product.company_id?.toString() || '',
        brand_id: product.brand_id?.toString() || '',
        category: product.category || '',
        sub_category: product.sub_category || '',
        description: product.description || '',
        target_crops: product.target_crops || '',
        target_problems: product.target_problems || '',
        dosage: product.dosage || '',
        usage_instructions: product.usage_instructions || '',
        safety_precautions: product.safety_precautions || '',
        price_range: product.price_range || '',
        is_active: product.is_active ?? true
      });
    } else {
      setEditingProduct(null);
      setFormData({
        name: '',
        organisation_id: '',
        company_id: '',
        brand_id: '',
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
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingProduct(null);
    setFormData({
      name: '',
      organisation_id: '',
      company_id: '',
      brand_id: '',
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

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error('Product name is required');
      return;
    }

    if (!formData.organisation_id || !formData.company_id || !formData.brand_id) {
      toast.error('Organisation, Company, and Brand are required');
      return;
    }

    try {
      const payload = {
        name: formData.name.trim(),
        organisation_id: parseInt(formData.organisation_id),
        company_id: parseInt(formData.company_id),
        brand_id: parseInt(formData.brand_id),
        category: formData.category.trim() || null,
        sub_category: formData.sub_category.trim() || null,
        description: formData.description.trim() || null,
        target_crops: formData.target_crops.trim() || null,
        target_problems: formData.target_problems.trim() || null,
        dosage: formData.dosage.trim() || null,
        usage_instructions: formData.usage_instructions.trim() || null,
        safety_precautions: formData.safety_precautions.trim() || null,
        price_range: formData.price_range.trim() || null,
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
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Failed to save product';

      if (Array.isArray(errorDetail)) {
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
      toast.error('Failed to delete product');
    }
  };

  const getBrandName = (brandId) => {
    const brand = brands.find(b => b.id === brandId);
    return brand?.name || 'Unknown Brand';
  };

  const getCompanyName = (companyId) => {
    const company = companies.find(c => c.id === companyId);
    return company?.name || 'Unknown Company';
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
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

    if (!uploadCompanyId || !uploadOrgId) {
      toast.error('Please select both an organisation and a company');
      return;
    }

    try {
      setUploading(true);
      const formDataObj = new FormData();
      formDataObj.append('file', csvFile);
      formDataObj.append('company_id', uploadCompanyId);

      const brand = brands.find(b => b.id.toString() === selectedBrandForUpload);
      if (brand) {
        formDataObj.append('brand_name', brand.name);
      }

      const response = await api.post('/products/upload-csv', formDataObj, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadResult(response.data);

      const hasErrors = response.data?.error_count > 0 || response.data?.errors?.length > 0;
      if (hasErrors) {
        toast.warning(
          `Imported: ${response.data?.success_count || 0}. Exists/Failed: ${response.data?.error_count || 0}`,
          { duration: 5000 }
        );
      } else {
        toast.success(
          `Products uploaded successfully! Imported: ${response.data?.success_count || 0}`,
        );
        setTimeout(() => {
          setUploadDialogOpen(false);
          setCsvFile(null);
          setUploadOrgId('');
          setUploadCompanyId('');
          setSelectedBrandForUpload('');
          setUploadResult(null);
        }, 1500);
      }

      setTimeout(() => {
        fetchProducts();
      }, 500);
    } catch (error) {
      console.error('Error uploading CSV:', error);
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Failed to upload CSV';

      if (Array.isArray(errorDetail)) {
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
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = async (type) => {
    try {
      const response = await api.get(`/products/import/template/${type}`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `products_template.${type === 'csv' ? 'csv' : 'xlsx'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error downloading template:', err);
      toast.error('Failed to download template');
    }
  };

  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.category?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.target_crops?.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
                Bulk Upload
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px] p-0 max-h-[90vh] overflow-y-auto w-[95vw]">
              <div className="p-6">
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <Upload className="h-6 w-6 text-purple-600" />
                    </div>
                    <div>
                      <DialogTitle className="text-xl font-bold text-gray-900">Bulk Upload Products</DialogTitle>
                      <DialogDescription className="text-sm text-gray-500 mt-1">
                        Upload CSV or Excel file to import multiple products
                      </DialogDescription>
                    </div>
                  </div>
                </div>

                <div className="space-y-6">
                  {/* Download Template */}
                  <div className="bg-blue-50/50 border border-blue-100 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <FileText className="h-5 w-5 text-blue-600" />
                      <div>
                        <h3 className="font-semibold text-blue-900 text-sm">Download Template</h3>
                        <p className="text-xs text-blue-600/80">Download a sample template to see the required format</p>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() => downloadTemplate('csv')}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 text-sm font-medium"
                      >
                        <Download className="h-4 w-4" />
                        CSV Template
                      </button>
                      <button
                        type="button"
                        onClick={() => downloadTemplate('excel')}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 text-sm font-medium"
                      >
                        <Download className="h-4 w-4" />
                        Excel Template
                      </button>
                    </div>
                  </div>

                  {/* Organisation Dropdown */}
                  <div>
                    <Label className="block text-sm font-medium text-gray-700 mb-2">
                      Organisation *
                    </Label>
                    <Select
                      value={uploadOrgId}
                      onValueChange={(value) => {
                        setUploadOrgId(value);
                        setUploadCompanyId('');
                        setSelectedBrandForUpload('');
                      }}
                      required
                    >
                      <SelectTrigger className="w-full h-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
                        <SelectValue placeholder="Select Organisation" />
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

                  {/* Company Dropdown */}
                  <div>
                    <Label className="block text-sm font-medium text-gray-700 mb-2">
                      Company *
                    </Label>
                    <Select
                      value={uploadCompanyId}
                      onValueChange={(value) => {
                        setUploadCompanyId(value);
                        setSelectedBrandForUpload('');
                      }}
                      required
                      disabled={!uploadOrgId || uploading}
                    >
                      <SelectTrigger className="w-full h-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
                        <SelectValue placeholder="Select Company to upload products for" />
                      </SelectTrigger>
                      <SelectContent>
                        {companies.filter(c => c.organisation_id === parseInt(uploadOrgId)).map((company) => (
                          <SelectItem key={company.id} value={company.id.toString()}>
                            {company.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-gray-500 mt-1">
                      All uploaded products will be associated with this company
                    </p>
                  </div>

                  {/* Brand Dropdown (Optional) */}
                  <div>
                    <Label className="block text-sm font-medium text-gray-700 mb-2">
                      Brand (Optional)
                    </Label>
                    <Select
                      value={selectedBrandForUpload}
                      onValueChange={(value) => setSelectedBrandForUpload(value)}
                      disabled={!uploadCompanyId || uploading}
                    >
                      <SelectTrigger className="w-full h-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
                        <SelectValue placeholder="Select Brand" />
                      </SelectTrigger>
                      <SelectContent>
                        {brands.filter(b => b.company_id === parseInt(uploadCompanyId)).map((brand) => (
                          <SelectItem key={brand.id} value={brand.id.toString()}>
                            {brand.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-gray-500 mt-1">
                      If left blank, the brand name from the CSV/Excel sheet will be used
                    </p>
                  </div>

                  {/* File Upload */}
                  <div>
                    <Label className="block text-sm font-medium text-gray-700 mb-2">
                      Select File *
                    </Label>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-500 transition-colors">
                      <Input
                        type="file"
                        accept=".csv,.xlsx,.xls"
                        onChange={handleFileChange}
                        className="hidden"
                        id="bulk-upload-file"
                        disabled={uploading}
                      />
                      <label
                        htmlFor="bulk-upload-file"
                        className="cursor-pointer flex flex-col items-center"
                      >
                        <Upload className="h-12 w-12 text-gray-400 mb-3" />
                        {csvFile ? (
                          <>
                            <p className="text-sm font-medium text-gray-900">{csvFile.name}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {(csvFile.size / 1024).toFixed(2)} KB
                            </p>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.preventDefault();
                                setCsvFile(null);
                              }}
                              className="mt-2 text-sm text-red-600 hover:text-red-700"
                            >
                              Remove file
                            </button>
                          </>
                        ) : (
                          <>
                            <p className="text-sm font-medium text-gray-900">
                              Click to upload or drag and drop
                            </p>
                            <p className="text-xs text-gray-500 mt-1">CSV or Excel (.xlsx, .xls)</p>
                          </>
                        )}
                      </label>
                    </div>
                  </div>

                  {/* Upload Result */}
                  {uploadResult && (
                    <div className={`p-4 rounded-lg ${uploadResult.success_count > 0 ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'}`}>
                      <h3 className="font-semibold text-gray-900 mb-2">Upload Results:</h3>
                      <div className="space-y-1 text-sm">
                        <p className="text-green-700">✅ Imported: {uploadResult.success_count} products</p>
                        <p className="text-red-700">❌ Failed: {uploadResult.error_count}</p>
                      </div>
                      {uploadResult.errors && uploadResult.errors.length > 0 && (
                        <div className="mt-3 max-h-32 overflow-y-auto">
                          <p className="text-xs font-semibold text-red-800 mb-1">Errors:</p>
                          {uploadResult.errors.map((err, idx) => (
                            <p key={idx} className="text-xs text-red-700">
                              {err}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Format Guide */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">Required Columns:</h3>
                    <ul className="text-xs text-gray-700 space-y-1 list-disc list-inside">
                      <li><span className="font-medium">name</span> - Product name</li>
                      <li><span className="font-medium">category</span> - Seeds, Fertilizers, Pesticides, etc.</li>
                    </ul>
                    <h3 className="text-sm font-semibold text-gray-900 mt-3 mb-2">Optional Columns:</h3>
                    <ul className="text-xs text-gray-700 space-y-1 list-disc list-inside">
                      <li>brand_name, sub_category, description, target_crops, target_problems</li>
                      <li>dosage, usage_instructions, safety_precautions, price_range, is_active</li>
                    </ul>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-3 pt-4 border-t border-gray-100">
                    <button
                      type="button"
                      onClick={() => {
                        setUploadDialogOpen(false);
                        setCsvFile(null);
                        setUploadOrgId('');
                        setUploadCompanyId('');
                        setSelectedBrandForUpload('');
                        setUploadResult(null);
                      }}
                      disabled={uploading}
                      className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-all disabled:opacity-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleCsvUpload}
                      disabled={uploading || !csvFile || !uploadCompanyId || !uploadOrgId}
                      className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-all disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {uploading ? (
                        <>
                          <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="h-4 w-4" />
                          Upload & Import
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
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
            <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
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

                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="organisation_id">Organisation *</Label>
                      <Select
                        value={formData.organisation_id}
                        onValueChange={(value) => setFormData({ ...formData, organisation_id: value, company_id: '', brand_id: '' })}
                        required
                      >
                        <SelectTrigger><SelectValue placeholder="Select organisation" /></SelectTrigger>
                        <SelectContent>
                          {organisations.map((org) => (
                            <SelectItem key={org.id} value={org.id.toString()}>{org.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid gap-2">
                      <Label htmlFor="company_id">Company *</Label>
                      <Select
                        value={formData.company_id}
                        onValueChange={(value) => setFormData({ ...formData, company_id: value, brand_id: '' })}
                        required
                        disabled={!formData.organisation_id}
                      >
                        <SelectTrigger><SelectValue placeholder="Select company" /></SelectTrigger>
                        <SelectContent>
                          {companies.filter(c => c.organisation_id === parseInt(formData.organisation_id)).map((company) => (
                            <SelectItem key={company.id} value={company.id.toString()}>{company.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="brand_id">Brand *</Label>
                    <Select
                      value={formData.brand_id}
                      onValueChange={(value) => setFormData({ ...formData, brand_id: value })}
                      required
                      disabled={!formData.company_id}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select brand" />
                      </SelectTrigger>
                      <SelectContent>
                        {brands.filter(b => b.company_id === parseInt(formData.company_id)).map((brand) => (
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

                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="category">Category *</Label>
                      <Select
                        value={formData.category}
                        onValueChange={(value) => setFormData({ ...formData, category: value, sub_category: '' })}
                        required
                      >
                        <SelectTrigger><SelectValue placeholder="Select Category" /></SelectTrigger>
                        <SelectContent>
                          {Object.keys(CATEGORY_OPTIONS).map((cat) => (
                            <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="sub_category">Sub Category *</Label>
                      <Select
                        value={formData.sub_category}
                        onValueChange={(value) => setFormData({ ...formData, sub_category: value })}
                        required
                        disabled={!formData.category}
                      >
                        <SelectTrigger><SelectValue placeholder="Select Sub Category" /></SelectTrigger>
                        <SelectContent>
                          {formData.category && CATEGORY_OPTIONS[formData.category]?.map((sub) => (
                            <SelectItem key={sub} value={sub}>{sub}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
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

                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="target_crops">Target Crops</Label>
                      <Input
                        id="target_crops"
                        value={formData.target_crops}
                        onChange={(e) => setFormData({ ...formData, target_crops: e.target.value })}
                        placeholder="e.g., Cotton, Wheat"
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="target_problems">Target Problems</Label>
                      <Input
                        id="target_problems"
                        value={formData.target_problems}
                        onChange={(e) => setFormData({ ...formData, target_problems: e.target.value })}
                        placeholder="e.g., Aphids, Whitefly, Leaf curl"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="dosage">Dosage Information</Label>
                      <Input
                        id="dosage"
                        value={formData.dosage}
                        onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                        placeholder="Recommended dosage"
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="price_range">Price Range *</Label>
                      <Input
                        id="price_range"
                        value={formData.price_range}
                        onChange={(e) => setFormData({ ...formData, price_range: e.target.value })}
                        placeholder="e.g., ₹500-1000"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="usage_instructions">Usage Instructions</Label>
                    <Textarea
                      id="usage_instructions"
                      value={formData.usage_instructions}
                      onChange={(e) => setFormData({ ...formData, usage_instructions: e.target.value })}
                      rows={2}
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="safety_precautions">Safety Precautions</Label>
                    <Textarea
                      id="safety_precautions"
                      value={formData.safety_precautions}
                      onChange={(e) => setFormData({ ...formData, safety_precautions: e.target.value })}
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
                      {getCompanyName(product.company_id)} - {getBrandName(product.brand_id)}
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
