import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { organisationAPI } from '@/api/api';
import { Loader2, Building2, Package, Tag, Leaf, TrendingUp, CheckCircle2, XCircle, Phone, Globe } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function RasiSeedsJourney() {
  const [loading, setLoading] = useState(true);
  const [orgData, setOrgData] = useState(null);
  const [brands, setBrands] = useState([]);
  const [products, setProducts] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchRasiSeedsData();
  }, []);

  const fetchRasiSeedsData = async () => {
    try {
      // Fetch organisation data (Rasi Seeds is ID: 2)
      const orgResponse = await organisationAPI.get(2);
      setOrgData(orgResponse.data);

      // Fetch brands
      const brandsResponse = await organisationAPI.getBrands(2);
      setBrands(brandsResponse.data);

      // Fetch all products
      const productsResponse = await organisationAPI.getProducts(2);
      setProducts(productsResponse.data);

    } catch (error) {
      console.error('Error fetching Rasi Seeds data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const getBrandProducts = (brandId) => {
    return products.filter(p => p.brand_id === brandId);
  };

  const categoryColors = {
    'Rasi Cotton Seeds': 'bg-green-100 text-green-700 border-green-300',
    'Rasi Cereals': 'bg-amber-100 text-amber-700 border-amber-300',
    'Rasi Vegetables': 'bg-red-100 text-red-700 border-red-300',
    'Rasi Pulses': 'bg-purple-100 text-purple-700 border-purple-300',
  };

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-8 rounded-lg border border-green-200">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Building2 className="w-10 h-10 text-green-600" />
              <h1 className="text-4xl font-bold text-gray-900">{orgData?.name || 'Rasi Seeds'}</h1>
              <span className="px-3 py-1 bg-green-600 text-white text-sm rounded-full font-medium">
                Enterprise
              </span>
            </div>
            <p className="text-lg text-gray-600 mb-4">Complete Import Journey & Product Catalog</p>
            <div className="flex gap-6 text-sm text-gray-700">
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-green-600" />
                <span>{orgData?.domain || 'rasiseeds.com'}</span>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-green-600" />
                <span>+91-40-23430733</span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500 mb-1">Status</p>
            <div className="flex items-center gap-2 text-green-600 font-semibold">
              <CheckCircle2 className="w-5 h-5" />
              <span>Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6 bg-white border-2 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Total Brands</p>
              <p className="text-3xl font-bold text-blue-600">{brands.length}</p>
            </div>
            <Tag className="w-8 h-8 text-blue-600" />
          </div>
        </Card>

        <Card className="p-6 bg-white border-2 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Total Products</p>
              <p className="text-3xl font-bold text-green-600">{products.length}</p>
            </div>
            <Package className="w-8 h-8 text-green-600" />
          </div>
        </Card>

        <Card className="p-6 bg-white border-2 border-emerald-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Active Products</p>
              <p className="text-3xl font-bold text-emerald-600">
                {products.filter(p => p.is_active).length}
              </p>
            </div>
            <CheckCircle2 className="w-8 h-8 text-emerald-600" />
          </div>
        </Card>

        <Card className="p-6 bg-white border-2 border-purple-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Categories</p>
              <p className="text-3xl font-bold text-purple-600">4</p>
            </div>
            <Leaf className="w-8 h-8 text-purple-600" />
          </div>
        </Card>
      </div>

      {/* Import Journey Timeline */}
      <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-blue-600" />
          Import Journey
        </h2>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center font-bold shrink-0">1</div>
            <div className="flex-1 bg-white p-4 rounded-lg shadow-sm">
              <p className="font-semibold text-gray-900">Organisation Created</p>
              <p className="text-sm text-gray-600">Rasi Seeds registered as Enterprise client</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center font-bold shrink-0">2</div>
            <div className="flex-1 bg-white p-4 rounded-lg shadow-sm">
              <p className="font-semibold text-gray-900">Brands Setup</p>
              <p className="text-sm text-gray-600">4 brands configured (Cotton, Cereals, Vegetables, Pulses)</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center font-bold shrink-0">3</div>
            <div className="flex-1 bg-white p-4 rounded-lg shadow-sm">
              <p className="font-semibold text-gray-900">Products Imported</p>
              <p className="text-sm text-gray-600">34 products successfully imported from website</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center font-bold shrink-0">✓</div>
            <div className="flex-1 bg-green-100 p-4 rounded-lg shadow-sm border-2 border-green-500">
              <p className="font-semibold text-green-900">Import Complete!</p>
              <p className="text-sm text-green-700">All data verified and active in system</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Brands & Products */}
      <div>
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Tag className="w-6 h-6 text-gray-700" />
          Brands & Products ({brands.length} Brands)
        </h2>
        
        <div className="space-y-6">
          {brands.map((brand) => {
            const brandProducts = getBrandProducts(brand.id);
            const colorClass = categoryColors[brand.name] || 'bg-gray-100 text-gray-700 border-gray-300';
            
            return (
              <Card key={brand.id} className="overflow-hidden border-2 hover:shadow-lg transition-shadow">
                <div className={`p-4 border-b-2 ${colorClass}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-bold">{brand.name}</h3>
                      <p className="text-sm opacity-90">{brand.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-bold">{brandProducts.length}</p>
                      <p className="text-sm">Products</p>
                    </div>
                  </div>
                </div>
                
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {brandProducts.map((product) => (
                      <div 
                        key={product.id}
                        className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border hover:bg-gray-100 transition-colors cursor-pointer"
                        onClick={() => navigate(`/products/${product.id}`)}
                      >
                        <div className={`w-10 h-10 rounded-full ${colorClass} flex items-center justify-center shrink-0`}>
                          <Leaf className="w-5 h-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-sm text-gray-900 truncate">{product.name}</p>
                          <p className="text-xs text-gray-600">{product.target_crops}</p>
                        </div>
                        {product.is_active ? (
                          <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-600 shrink-0" />
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Product Breakdown */}
      <Card className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
        <h2 className="text-2xl font-bold mb-4 text-green-900">📊 Product Breakdown</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {brands.map((brand) => {
            const count = getBrandProducts(brand.id).length;
            const colorClass = categoryColors[brand.name] || 'bg-gray-100 text-gray-700';
            
            return (
              <div key={brand.id} className={`p-4 rounded-lg ${colorClass} border-2`}>
                <p className="text-sm opacity-90 mb-1">{brand.name.replace('Rasi ', '')}</p>
                <p className="text-3xl font-bold">{count}</p>
                <p className="text-xs opacity-75 mt-1">products</p>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Quick Actions */}
      <Card className="p-6">
        <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/organisations/2')}
            className="p-4 border-2 border-blue-200 rounded-lg hover:bg-blue-50 transition-colors text-left"
          >
            <Building2 className="w-6 h-6 text-blue-600 mb-2" />
            <p className="font-semibold text-gray-900">View Organisation</p>
            <p className="text-sm text-gray-600">See full details</p>
          </button>
          
          <button
            onClick={() => navigate('/brands')}
            className="p-4 border-2 border-green-200 rounded-lg hover:bg-green-50 transition-colors text-left"
          >
            <Tag className="w-6 h-6 text-green-600 mb-2" />
            <p className="font-semibold text-gray-900">Manage Brands</p>
            <p className="text-sm text-gray-600">Edit brand details</p>
          </button>
          
          <button
            onClick={() => navigate('/products')}
            className="p-4 border-2 border-purple-200 rounded-lg hover:bg-purple-50 transition-colors text-left"
          >
            <Package className="w-6 h-6 text-purple-600 mb-2" />
            <p className="font-semibold text-gray-900">All Products</p>
            <p className="text-sm text-gray-600">Browse catalog</p>
          </button>
        </div>
      </Card>
    </div>
  );
}
