// Organisation Detail View - Super Admin Governance & Safety
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Building2,
  Phone,
  Package,
  TrendingUp,
  Database,
  PhoneCall,
  Shield,
  ArrowLeft,
  AlertTriangle,
  CheckCircle,
  Users,
  Activity
} from 'lucide-react';
import api from '../api/api';
import WebsiteProductImporter from '../components/WebsiteProductImporter';

const OrganisationDetailView = () => {
  const { orgId } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [organisation, setOrganisation] = useState(null);
  const [brands, setBrands] = useState([]);
  const [products, setProducts] = useState([]);
  const [phoneNumbers, setPhoneNumbers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrganisationDetails();
  }, [orgId]);

  const fetchOrganisationDetails = async () => {
    try {
      setLoading(true);
      // Fetch org stats
      const statsResponse = await api.get('/superadmin/organisations/stats');
      const org = statsResponse.data.find(o => o.id === parseInt(orgId));
      setOrganisation(org);

      // Fetch brands
      const brandsResponse = await api.get(`/organisations/${orgId}/brands`);
      setBrands(brandsResponse.data);

      // Fetch all products for this org
      const allProducts = [];
      for (const brand of brandsResponse.data) {
        const productsResponse = await api.get(`/brands/${brand.id}/products`);
        allProducts.push(...productsResponse.data.map(p => ({ ...p, brand_name: brand.name })));
      }
      setProducts(allProducts);

      // Fetch phone numbers
      const phonesResponse = await api.get(`/superadmin/organisations/${orgId}/phone-numbers`);
      setPhoneNumbers(phonesResponse.data);
    } catch (error) {
      console.error('Error fetching organisation details:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleOrganisationStatus = async () => {
    if (!window.confirm(
      organisation.is_active
        ? '⚠️ CRITICAL: Inactivate this organisation? All services will stop immediately.'
        : 'Activate this organisation? Their services will resume.'
    )) return;

    try {
      await api.patch(`/superadmin/organisations/${orgId}/status`, {
        is_active: !organisation.is_active
      });
      setOrganisation({ ...organisation, is_active: !organisation.is_active });
    } catch (error) {
      console.error('Error toggling status:', error);
      alert('Failed to update status');
    }
  };

  const banProductGlobally = async (product) => {
    const reason = window.prompt(
      `🚨 BAN PRODUCT GLOBALLY:\n\nProduct: ${product.name}\nCompany: ${product.brand_name}\n\nThis will block AI from suggesting this product to ANY organisation.\n\nEnter ban reason (regulatory/safety):`,
      'Safety concern - under investigation'
    );

    if (!reason) return;

    try {
      await api.post('/superadmin/banned-products', {
        product_name: product.name,
        chemical_name: product.chemical_name || '',
        ban_reason: reason,
        regulatory_reference: '',
        expiry_date: null
      });
      alert(`✅ Product "${product.name}" banned globally!\n\nAI will no longer suggest this product to any organisation.`);
      fetchOrganisationDetails();
    } catch (error) {
      console.error('Error banning product:', error);
      alert('Failed to ban product');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading organisation details...</p>
        </div>
      </div>
    );
  }

  if (!organisation) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border-l-4 border-red-500 p-6 rounded-lg">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-red-600" />
            <div>
              <h3 className="text-red-800 font-bold">Organisation Not Found</h3>
              <p className="text-red-700">Invalid organisation ID</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/superadmin/organisations-platform')}
            className="p-2 hover:bg-gray-200 rounded-lg transition-all"
          >
            <ArrowLeft className="h-6 w-6 text-gray-600" />
          </button>
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl shadow-lg ${organisation.is_active
              ? 'bg-gradient-to-br from-blue-500 to-indigo-600'
              : 'bg-gradient-to-br from-gray-400 to-gray-600'
              }`}>
              <Building2 className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{organisation.name}</h1>
              <div className="flex items-center gap-3 mt-1">
                {organisation.is_active ? (
                  <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-semibold rounded-full flex items-center gap-1">
                    <CheckCircle className="h-4 w-4" />
                    Active
                  </span>
                ) : (
                  <span className="px-3 py-1 bg-red-100 text-red-800 text-sm font-semibold rounded-full flex items-center gap-1">
                    <AlertTriangle className="h-4 w-4" />
                    Inactive
                  </span>
                )}
                <span className="text-gray-500 text-sm">ID: {organisation.id}</span>
              </div>
            </div>
          </div>
        </div>

        <button
          onClick={toggleOrganisationStatus}
          className={`px-6 py-3 rounded-lg font-semibold transition-all ${organisation.is_active
            ? 'bg-red-600 hover:bg-red-700 text-white'
            : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
        >
          {organisation.is_active ? '⚠️ Inactive Organisation' : '✅ Activate Organisation'}
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Brands</p>
              <p className="text-3xl font-bold text-purple-600">{organisation.brand_count || 0}</p>
            </div>
            <Package className="h-10 w-10 text-purple-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Products</p>
              <p className="text-3xl font-bold text-green-600">{organisation.product_count || 0}</p>
            </div>
            <TrendingUp className="h-10 w-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Phone Numbers</p>
              <p className="text-3xl font-bold text-blue-600">{organisation.phone_count || 0}</p>
            </div>
            <Phone className="h-10 w-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Calls</p>
              <p className="text-3xl font-bold text-indigo-600">{organisation.call_count || 0}</p>
            </div>
            <PhoneCall className="h-10 w-10 text-indigo-500" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="flex border-b border-gray-200">
          {[
            { id: 'overview', label: 'Overview', icon: Building2 },
            { id: 'import', label: 'Import Products', icon: Database },
            { id: 'phones', label: 'Phone Numbers', icon: Phone },
            { id: 'brands', label: 'Brands', icon: Package },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-4 font-medium transition-all ${activeTab === tab.id
                ? 'border-b-4 border-indigo-600 text-indigo-600 bg-indigo-50'
                : 'text-gray-600 hover:bg-gray-50'
                }`}
            >
              <tab.icon className="h-5 w-5" />
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Organisation Name</p>
                  <p className="text-lg font-bold text-gray-900">{organisation.name}</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Status</p>
                  <p className={`text-lg font-bold ${organisation.is_active ? 'text-green-600' : 'text-red-600'}`}>
                    {organisation.is_active ? 'Active' : 'Inactive'}
                  </p>
                </div>
              </div>

              <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                <div className="flex items-start gap-3">
                  <Shield className="h-6 w-6 text-blue-600 mt-1" />
                  <div>
                    <h4 className="font-bold text-blue-900 mb-1">Governance Mode</h4>
                    <p className="text-blue-800 text-sm">
                      As Super Admin, you have read-only visibility with critical safety controls.
                      You can manage brands and phone numbers, or inactivate the entire organisation if needed.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Import Products Tab */}
          {activeTab === 'import' && (
            <div>
              <WebsiteProductImporter
                organisationId={orgId}
                onImportComplete={() => {
                  // Refresh organisation details after import
                  fetchOrganisationDetails();
                }}
              />
            </div>
          )}

          {/* Phone Numbers Tab */}
          {activeTab === 'phones' && (
            <div>
              <h3 className="text-lg font-bold mb-4">Phone Numbers ({phoneNumbers.length})</h3>
              {phoneNumbers.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No phone numbers configured</p>
              ) : (
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Phone Number</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {phoneNumbers.map(phone => (
                      <tr key={phone.id}>
                        <td className="px-4 py-3 font-mono">{phone.phone_number}</td>
                        <td className="px-4 py-3 text-center">
                          {phone.is_active ? (
                            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">Active</span>
                          ) : (
                            <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs font-semibold rounded">Inactive</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* Brands Tab */}
          {activeTab === 'brands' && (
            <div>
              <h3 className="text-lg font-bold mb-4">Brands ({brands.length}) - View Only</h3>
              {brands.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No brands registered</p>
              ) : (
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Brand Name</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Products</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {brands.map(brand => (
                      <tr key={brand.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <Package className="h-5 w-5 text-purple-500" />
                            <span className="font-medium">{brand.name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          {products.filter(p => p.brand_name === brand.name).length}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">Active</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}


        </div>
      </div>
    </div>
  );
};

export default OrganisationDetailView;
