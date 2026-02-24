// Organisation Admin Dashboard
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, 
  Package, 
  Tag, 
  TrendingUp, 
  ShoppingBag,
  Plus,
  Edit,
  Eye,
  AlertCircle,
  Upload,
  FileText,
  Download
} from 'lucide-react';
import api from '../api/api';
import { kbUploadAPI } from '../api/kbUploadAPI';
  
const OrganisationDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [brandName, setBrandName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  // KB Upload dialog state
  const [showKBUploadDialog, setShowKBUploadDialog] = useState(false);
  const [kbUploadFile, setKBUploadFile] = useState();
  const [kbUploading, setKBUploading] = useState(false);

  // Try to get orgId from stats or user context (fallback: null)
  const orgId = stats?.organisation_id || null;

  // Handle KB upload
  const handleKBUpload = async () => {
    if (!kbUploadFile || !orgId) {
      alert('Please select a file');
      return;
    }
    setKBUploading(true);
    try {
      await kbUploadAPI.upload(kbUploadFile, orgId);
      alert('KB uploaded successfully');
      setShowKBUploadDialog(false);
      setKBUploadFile(null);
    } catch (e) {
      alert('Upload failed: ' + (e?.response?.data?.detail || 'Unknown error'));
    } finally {
      setKBUploading(false);
    }
  };


  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setLoading(true);
      const response = await api.get('/org-admin/dashboard/stats');
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching dashboard stats:', err);
      setError(err.response?.data?.detail || 'Failed to load dashboard');
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
    if (!uploadFile) {
      alert('Please select a file');
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      if (brandName.trim()) {
        formData.append('brand_name', brandName.trim());
      }

      const response = await api.post('/org-admin/products/import/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setUploadResult(response.data);
      
      // Refresh stats
      await fetchDashboardStats();
      
      // Show success message
      alert(response.data.message);
      
      // Reset form if successful
      if (response.data.results.imported > 0) {
        setUploadFile(null);
        setBrandName('');
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
      const response = await api.get(`/org-admin/products/import/template/${type}`, {
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
          <AlertCircle className="h-5 w-5 text-red-600 mr-3 mt-0.5" />
          <div>
            <h3 className="text-red-800 font-medium">Error Loading Dashboard</h3>
            <p className="text-red-600 text-sm mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Brands',
      value: stats?.total_brands || 0,
      icon: Tag,
      color: 'bg-blue-500',
      action: () => navigate('/org-admin/brands')
    },
    {
      title: 'Total Products',
      value: stats?.total_products || 0,
      icon: Package,
      color: 'bg-green-500',
      action: () => navigate('/org-admin/products')
    },
    {
      title: 'Active Products',
      value: stats?.active_products || 0,
      icon: ShoppingBag,
      color: 'bg-indigo-500',
      action: () => navigate('/org-admin/products?status=active')
    },
    {
      title: 'Categories',
      value: stats?.categories || 0,
      icon: TrendingUp,
      color: 'bg-purple-500',
      action: null
    }
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Organisation Dashboard</h1>
          <p className="text-gray-600 mt-1">Manage your brands, products and profile</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowKBUploadDialog(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            <Upload className="h-4 w-4" />
            Add KB Data
          </button>
          <button
            onClick={() => navigate('/org-admin/profile')}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            <Edit className="h-4 w-4" />
            Edit Profile
          </button>
        </div>
      </div>
      {/* KB Upload Dialog */}
      {showKBUploadDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Upload className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Upload Knowledge Base Data</h2>
                  <p className="text-sm text-gray-600">Upload PDF or CSV to add KB entries for your organisation</p>
                </div>
              </div>
            </div>
            <div className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium mb-1">File (PDF or CSV)</label>
                <input
                  type="file"
                  accept=".pdf,.csv,application/pdf,text/csv"
                  onChange={e => setKBUploadFile(e.target.files[0])}
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowKBUploadDialog(false)}
                  disabled={kbUploading}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-all disabled:opacity-50"
                >Cancel</button>
                <button
                  onClick={handleKBUpload}
                  disabled={kbUploading || !kbUploadFile}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-all disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {kbUploading ? (
                    <>
                      <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4" />
                      Upload
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, index) => (
          <div
            key={index}
            onClick={card.action}
            className={`bg-white rounded-xl shadow-md p-6 ${card.action ? 'cursor-pointer hover:shadow-lg transition-shadow' : ''}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">{card.title}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{card.value}</p>
              </div>
              <div className={`${card.color} p-3 rounded-lg`}>
                <card.icon className="h-6 w-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/org-admin/brands/new')}
            className="flex items-center gap-3 p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-colors"
          >
            <Plus className="h-5 w-5 text-indigo-600" />
            <span className="font-medium text-gray-700">Add New Brand</span>
          </button>
          <button
            onClick={() => navigate('/org-admin/products/new')}
            className="flex items-center gap-3 p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors"
          >
            <Plus className="h-5 w-5 text-green-600" />
            <span className="font-medium text-gray-700">Add New Product</span>
          </button>
          <button
            onClick={() => navigate('/org-admin/products')}
            className="flex items-center gap-3 p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
          >
            <Eye className="h-5 w-5 text-blue-600" />
            <span className="font-medium text-gray-700">View All Products</span>
          </button>
        </div>
      </div>

      {/* Recent Products */}
      {stats?.recent_products && stats.recent_products.length > 0 && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-900">Recent Products</h2>
            <button
              onClick={() => navigate('/org-admin/products')}
              className="text-indigo-600 hover:text-indigo-700 font-medium text-sm"
            >
              View All →
            </button>
          </div>
          <div className="space-y-3">
            {stats.recent_products.map((product) => (
              <div
                key={product.id}
                onClick={() => navigate(`/org-admin/products/${product.id}`)}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900">{product.name}</h3>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-sm text-gray-600">{product.category}</span>
                    {product.sub_category && (
                      <>
                        <span className="text-gray-400">•</span>
                        <span className="text-sm text-gray-600">{product.sub_category}</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {product.is_active ? (
                    <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                      Active
                    </span>
                  ) : (
                    <span className="px-3 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">
                      Inactive
                    </span>
                  )}
                  <Eye className="h-4 w-4 text-gray-400" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {stats?.total_products === 0 && (
        <div className="bg-white rounded-xl shadow-md p-12 text-center">
          <Package className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-900 mb-2">No Products Yet</h3>
          <p className="text-gray-600 mb-6">Get started by creating your first brand and adding products</p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => navigate('/org-admin/brands/new')}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
            >
              Create Brand
            </button>
            <button
              onClick={() => navigate('/org-admin/products/new')}
              className="px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
            >
              Add Product
            </button>
          </div>
        </div>
      )}
      
      {/* CSV/Excel Upload Modal */}
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
                    Download CSV Template
                  </button>
                  <button
                    onClick={() => downloadTemplate('excel')}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 text-sm font-medium"
                  >
                    <Download className="h-4 w-4" />
                    Download Excel Template
                  </button>
                </div>
              </div>

              {/* Default Brand Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Default Brand Name (Optional)
                </label>
                <input
                  type="text"
                  value={brandName}
                  onChange={(e) => setBrandName(e.target.value)}
                  placeholder="e.g., My Brand"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  disabled={uploading}
                />
                <p className="text-xs text-gray-500 mt-1">
                  If your CSV doesn't have 'brand_name' column, this will be used as default
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
                    id="product-file-upload"
                    disabled={uploading}
                  />
                  <label
                    htmlFor="product-file-upload"
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
                <div className={`p-4 rounded-lg ${
                  uploadResult.results.imported > 0 ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'
                }`}>
                  <h3 className="font-semibold text-gray-900 mb-2">Upload Results:</h3>
                  <div className="space-y-1 text-sm">
                    <p className="text-green-700">✅ Imported: {uploadResult.results.imported} products</p>
                    <p className="text-gray-700">⏭️ Skipped: {uploadResult.results.skipped} (already exist)</p>
                    <p className="text-red-700">❌ Failed: {uploadResult.results.failed}</p>
                    {uploadResult.results.created_brands.length > 0 && (
                      <p className="text-blue-700">
                        🏷️ Brands created: {uploadResult.results.created_brands.join(', ')}
                      </p>
                    )}
                  </div>
                  {uploadResult.results.errors.length > 0 && (
                    <div className="mt-3 max-h-32 overflow-y-auto">
                      <p className="text-xs font-semibold text-red-800 mb-1">Errors:</p>
                      {uploadResult.results.errors.slice(0, 5).map((err, idx) => (
                        <p key={idx} className="text-xs text-red-700">
                          Row {err.row}: {err.error}
                        </p>
                      ))}
                      {uploadResult.results.errors.length > 5 && (
                        <p className="text-xs text-red-600 mt-1">
                          ... and {uploadResult.results.errors.length - 5} more errors
                        </p>
                      )}
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
                  <li>brand_name, sub_category, description, composition</li>
                  <li>dosage, benefits, target_crops, pack_size, mrp, is_active</li>
                </ul>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    setShowUploadModal(false);
                    setUploadFile(null);
                    setBrandName('');
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

export default OrganisationDashboard;
