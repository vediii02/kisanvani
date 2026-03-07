// Organisation Products Management
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Package, Plus, Edit2, Trash2, Search, Filter, AlertCircle, X, Upload, Download, FileText } from 'lucide-react';
import api from '../api/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

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

const OrganisationProducts = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [brands, setBrands] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterBrand, setFilterBrand] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [brandName, setBrandName] = useState('');
  const [uploadCompanyId, setUploadCompanyId] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [formData, setFormData] = useState({
    company_id: '',
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
    price: '',
    is_active: true
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [productsRes, brandsRes, companiesRes] = await Promise.all([
        api.get('/products'),
        api.get('/brands'),
        api.get('/organisation/companies')
      ]);
      setProducts(productsRes.data);
      setBrands(brandsRes.data);
      setCompanies(companiesRes.data.companies || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      const validTypes = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      ];

      if (!validTypes.includes(file.type) &&
        !file.name.endsWith('.csv') &&
        !file.name.endsWith('.xlsx') &&
        !file.name.endsWith('.xls')) {
        alert('Please select a CSV or Excel file');
        return;
      }

      setUploadFile(file);
      setUploadResult(null);
    }
  };

  const handleUploadProducts = async () => {
    if (!uploadCompanyId) {
      alert('Please select a company');
      return;
    }

    if (!uploadFile) {
      alert('Please select a file');
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('company_id', uploadCompanyId);
      if (brandName.trim()) {
        formData.append('brand_name', brandName.trim());
      }

      const response = await api.post('/products/upload-csv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setUploadResult(response.data);

      // Refresh products list
      await fetchData();

      // Show success message
      alert(response.data.message);

      // Reset form if successful
      if (response.data.success_count > 0) {
        setUploadFile(null);
        setBrandName('');
        setUploadCompanyId('');
        setShowUploadModal(false);
      }
    } catch (err) {
      console.error('Error uploading products:', err);
      const errorMsg = err.response?.data?.detail || 'Failed to upload products';
      alert(`Error: ${errorMsg}`);
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
      alert('Failed to download template');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const submitData = {
        ...formData,
        company_id: parseInt(formData.company_id),
        brand_id: formData.brand_id ? parseInt(formData.brand_id) : null,
        organisation_id: 1 // Will be set by backend from JWT
      };

      if (editingProduct) {
        await api.put(`/products/${editingProduct.id}`, submitData);
      } else {
        await api.post('/products', submitData);
      }

      setShowAddModal(false);
      setEditingProduct(null);
      resetForm();
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save product');
    }
  };

  const resetForm = () => {
    setFormData({
      company_id: '',
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
      price: '',
      is_active: true
    });
  };

  const handleEdit = (product) => {
    setEditingProduct(product);

    // Normalize category and sub-category
    let selectedCategory = product.category || '';
    let selectedSubCategory = product.sub_category || '';

    // If the category is actually a sub-category, find its parent
    if (selectedCategory && !CATEGORY_OPTIONS[selectedCategory]) {
      for (const [parentCat, subCats] of Object.entries(CATEGORY_OPTIONS)) {
        if (subCats.includes(selectedCategory)) {
          selectedSubCategory = selectedCategory;
          selectedCategory = parentCat;
          break;
        }
      }
    }

    setFormData({
      company_id: product.company_id?.toString() || '',
      brand_id: product.brand_id?.toString() || '',
      name: product.name,
      category: selectedCategory,
      sub_category: selectedSubCategory,
      description: product.description || '',
      target_crops: product.target_crops || '',
      target_problems: product.target_problems || '',
      dosage: product.dosage || '',
      usage_instructions: product.usage_instructions || '',
      safety_precautions: product.safety_precautions || '',
      price_range: product.price_range || '',
      price: product.price || '',
      is_active: product.is_active
    });
    setShowAddModal(true);
  };

  const handleDelete = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;

    try {
      await api.delete(`/products/${productId}`);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete product');
    }
  };

  // Get unique categories
  const categories = [...new Set(products.map(p => p.category).filter(Boolean))];

  // Filter products
  const filteredProducts = products.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesBrand = !filterBrand || product.brand_id === parseInt(filterBrand);
    const matchesCategory = !filterCategory || product.category === filterCategory;
    const matchesStatus = !filterStatus || (filterStatus === 'active' ? product.is_active : !product.is_active);
    return matchesSearch && matchesBrand && matchesCategory && matchesStatus;
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Package className="w-8 h-8 text-primary" />
            Products Management
          </h1>
          <Badge variant="secondary" className="mt-1 bg-purple-100 text-purple-700">{products.length} Total Products</Badge>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            <Upload className="h-4 w-4" />
            Bulk Upload
          </button>
          <button
            onClick={() => {
              setEditingProduct(null);
              resetForm();
              setShowAddModal(true);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            Add Product
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
          <AlertCircle className="h-5 w-5 text-red-600 mr-3 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-red-800 font-medium">Error</h3>
            <p className="text-red-600 text-sm mt-1">{error}</p>
          </div>
          <button onClick={() => setError('')} className="text-red-600 hover:text-red-700">
            <X className="h-5 w-5" />
          </button>
        </div>
      )}

      {/* Search and Filters */}
      <div className="bg-white rounded-xl shadow-md p-4 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select
            value={filterBrand}
            onChange={(e) => setFilterBrand(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="">All Brands</option>
            {brands.map(brand => (
              <option key={brand.id} value={brand.id}>{brand.name}</option>
            ))}
          </select>

          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Products List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : filteredProducts.length === 0 ? (
        <div className="bg-white rounded-xl shadow-md p-12 text-center">
          <Package className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-900 mb-2">No Products Found</h3>
          <p className="text-gray-600 mb-6">
            {searchTerm || filterBrand || filterCategory || filterStatus
              ? 'Try adjusting your filters'
              : 'Get started by adding your first product'}
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Company
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Brand
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Target Crops
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredProducts.map((product) => (
                <tr key={product.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{product.name}</div>
                    {product.sub_category && (
                      <div className="text-sm text-gray-500">{product.sub_category}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {product.company_name ? (
                      <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-xs font-medium">
                        {product.company_name}
                      </span>
                    ) : (
                      <span className="text-gray-400 italic">Organisation</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {product.brand_name || 'N/A'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {product.category}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {product.price ? `₹${product.price}` : (product.price_range || '-')}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 text-truncate max-w-xs">
                    {product.target_crops || '-'}
                  </td>
                  <td className="px-6 py-4">
                    {product.is_active ? (
                      <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right text-sm font-medium flex justify-end gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => handleEdit(product)}
                      title="Edit"
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      className="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDelete(product.id)}
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-2xl m-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {editingProduct ? 'Edit Product' : 'Add New Product'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Company *</label>
                  <select
                    value={formData.company_id}
                    onChange={(e) => setFormData({ ...formData, company_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    required
                  >
                    <option value="" disabled>Select Company *</option>
                    {companies.map(company => (
                      <option key={company.id} value={company.id}>{company.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Brand *</label>
                  <select
                    value={formData.brand_id}
                    onChange={(e) => setFormData({ ...formData, brand_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    required
                  >
                    <option value="">Select Brand </option>
                    {brands
                      .filter(b => !formData.company_id || b.company_id === parseInt(formData.company_id))
                      .map(brand => (
                        <option key={brand.id} value={brand.id}>{brand.name}</option>
                      ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value, sub_category: '' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    required
                  >
                    <option value="" disabled>Select Category</option>
                    {Object.keys(CATEGORY_OPTIONS).map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sub Category *</label>
                  <select
                    value={formData.sub_category}
                    onChange={(e) => setFormData({ ...formData, sub_category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    disabled={!formData.category}
                    required
                  >
                    <option value="" disabled>Select Sub Category</option>
                    {formData.category && CATEGORY_OPTIONS[formData.category]?.map((sub) => (
                      <option key={sub} value={sub}>{sub}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Target Crops</label>
                  <input
                    type="text"
                    value={formData.target_crops}
                    onChange={(e) => setFormData({ ...formData, target_crops: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="e.g., Cotton, Wheat"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Target Problems</label>
                  <input
                    type="text"
                    value={formData.target_problems}
                    onChange={(e) => setFormData({ ...formData, target_problems: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dosage</label>
                  <input
                    type="text"
                    value={formData.dosage}
                    onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="e.g., 450"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price Range</label>
                  <input
                    type="text"
                    value={formData.price_range}
                    onChange={(e) => setFormData({ ...formData, price_range: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="e.g., 400-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Usage Instructions</label>
                <textarea
                  value={formData.usage_instructions}
                  onChange={(e) => setFormData({ ...formData, usage_instructions: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Safety Precautions</label>
                <textarea
                  value={formData.safety_precautions}
                  onChange={(e) => setFormData({ ...formData, safety_precautions: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
                  Active
                </label>
              </div>

              <div className="flex gap-3 pt-4 sticky bottom-0 bg-white">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false);
                    setEditingProduct(null);
                    resetForm();
                  }}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  {editingProduct ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Upload className="h-6 w-6 text-purple-600" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">Bulk Upload Products</h2>
                    <p className="text-sm text-gray-600">Upload CSV or Excel file to import multiple products</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setShowUploadModal(false);
                    setUploadFile(null);
                    setBrandName('');
                    setUploadCompanyId('');
                    setUploadResult(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Download Templates */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-blue-900 mb-3 flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Download Template
                </h3>
                <p className="text-xs text-blue-800 mb-3">
                  Download a sample template to see the required format
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => downloadTemplate('csv')}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 text-sm font-medium"
                  >
                    <Download className="h-4 w-4" />
                    CSV Template
                  </button>
                  <button
                    onClick={() => downloadTemplate('excel')}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 text-sm font-medium"
                  >
                    <Download className="h-4 w-4" />
                    Excel Template
                  </button>
                </div>
              </div>

              {/* Select Company */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Company *
                </label>
                <select
                  value={uploadCompanyId}
                  onChange={(e) => {
                    const companyId = e.target.value;
                    setUploadCompanyId(companyId);
                    setBrandName(''); // Reset brand selection when company changes
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  disabled={uploading}
                  required
                >
                  <option value="" disabled>Select Company to upload products for</option>
                  {companies.map((company) => (
                    <option key={company.id} value={company.id}>
                      {company.name}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  All uploaded products will be associated with this company
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Brand (Optional)
                </label>
                <select
                  value={brandName}
                  onChange={(e) => setBrandName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  disabled={!uploadCompanyId || uploading}
                >
                  <option value="">Select Brand (Optional)</option>
                  {brands
                    .filter(b => b.company_id === parseInt(uploadCompanyId))
                    .map(brand => (
                      <option key={brand.id} value={brand.name}>{brand.name}</option>
                    ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  If your CSV doesn't have 'brand_name' column, this selection will be used
                </p>
              </div>

              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select File *
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-500 transition-colors">
                  <input
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="bulk-upload-file"
                    disabled={uploading}
                  />
                  <label
                    htmlFor="bulk-upload-file"
                    className="cursor-pointer flex flex-col items-center"
                  >
                    <Upload className="h-12 w-12 text-gray-400 mb-3" />
                    {uploadFile ? (
                      <>
                        <p className="text-sm font-medium text-gray-900">{uploadFile.name}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {(uploadFile.size / 1024).toFixed(2)} KB
                        </p>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            setUploadFile(null);
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
                <div className={`p-4 rounded-lg ${uploadResult.success_count > 0 ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'
                  }`}>
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
                  <li><span className="font-medium">category</span> - Seeds, Fertilizers, Pesticides</li>
                </ul>
                <h3 className="text-sm font-semibold text-gray-900 mt-3 mb-2">Optional Columns:</h3>
                <ul className="text-xs text-gray-700 space-y-1 list-disc list-inside">
                  <li>brand_name, sub_category, description, composition</li>
                  <li>dosage, benefits, target_crops, pack_size, mrp</li>
                </ul>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    setShowUploadModal(false);
                    setUploadFile(null);
                    setBrandName('');
                    setUploadCompanyId('');
                    setUploadResult(null);
                  }}
                  disabled={uploading}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-all disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUploadProducts}
                  disabled={uploading || !uploadFile}
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
        </div>
      )}
    </div>
  );
};

export default OrganisationProducts;
