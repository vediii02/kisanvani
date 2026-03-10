// Organisation Detail View - Super Admin Governance & Safety
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Building2,
  Phone,
  Package,
  Tag,
  PhoneCall,
  Shield,
  ArrowLeft,
  AlertTriangle,
  CheckCircle,
  Mail,
  MapPin,
  Globe,
  Calendar,
  User,
  Briefcase,
  Hash,
  Crown,
  Store,
  Loader2,
  Info
} from 'lucide-react';
import api from '../api/api';

const OrganisationDetailView = () => {
  const { orgId } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [organisation, setOrganisation] = useState(null);
  const [brands, setBrands] = useState([]);
  const [products, setProducts] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [phoneNumbers, setPhoneNumbers] = useState([]);
  const [callLogs, setCallLogs] = useState([]);
  const [callsLoading, setCallsLoading] = useState(false);
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

      // Fetch all data in parallel
      const [brandsRes, productsRes, companiesRes, phonesRes, callsRes] = await Promise.allSettled([
        api.get(`/organisations/${orgId}/brands`),
        api.get(`/superadmin/organisations/${orgId}/products`),
        api.get(`/admin/companies?organisation_id=${orgId}`),
        api.get(`/superadmin/organisations/${orgId}/phone-numbers`),
        api.get(`/superadmin/calls?organisation_id=${orgId}`),
      ]);

      setBrands(brandsRes.status === 'fulfilled' ? brandsRes.value.data : []);
      setProducts(productsRes.status === 'fulfilled' ? productsRes.value.data : []);
      setCompanies(companiesRes.status === 'fulfilled' ? companiesRes.value.data || [] : []);
      setPhoneNumbers(phonesRes.status === 'fulfilled' ? phonesRes.value.data : []);
      setCallLogs(callsRes.status === 'fulfilled' ? callsRes.value.data : []);
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

  const totalPhoneNumbers = companies.reduce((acc, company) => {
    let count = 0;
    if (company.phone && company.phone.trim() !== '') count++;
    if (company.secondary_phone && company.secondary_phone.trim() !== '') count++;
    return acc + count;
  }, 0);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Building2 },
    { id: 'companies', label: `Companies (${organisation.company_count || companies.length || 0})`, icon: Store },
    { id: 'brands', label: `Brands (${organisation.brand_count || 0})`, icon: Tag },
    { id: 'products', label: `Products (${organisation.product_count || 0})`, icon: Package },
    { id: 'phones', label: `Phone Numbers (${totalPhoneNumbers})`, icon: Phone },
    { id: 'calls', label: `Total Calls (${organisation.call_count || callLogs.length || 0})`, icon: PhoneCall },
  ];

  const DetailItem = ({ icon: Icon, label, value, color = 'text-gray-900' }) => (
    <div className="flex flex-col gap-1.5 transition-all hover:translate-x-1">
      <div className="flex items-center gap-2 group">
        {Icon && <Icon className="h-4 w-4 text-indigo-400 group-hover:text-indigo-600 transition-colors" />}
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">{label}</p>
      </div>
      <p className={`text-base font-bold tracking-tight ${color}`}>{value || '—'}</p>
    </div>
  );

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
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Companies</p>
              <p className="text-3xl font-bold text-gray-600">{organisation.company_count || companies.length || 0}</p>
            </div>
            <Store className="h-10 w-10 text-gray-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Brands</p>
              <p className="text-3xl font-bold text-purple-600">{organisation.brand_count || 0}</p>
            </div>
            <Tag className="h-10 w-10 text-purple-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Products</p>
              <p className="text-3xl font-bold text-green-600">{organisation.product_count || 0}</p>
            </div>
            <Package className="h-10 w-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Phone Numbers</p>
              <p className="text-3xl font-bold text-blue-600">{totalPhoneNumbers}</p>
            </div>
            <Phone className="h-10 w-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Calls</p>
              <p className="text-3xl font-bold text-indigo-600">{organisation.call_count || callLogs.length || 0}</p>
            </div>
            <PhoneCall className="h-10 w-10 text-indigo-500" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="flex border-b border-gray-200 overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-4 font-medium transition-all whitespace-nowrap ${activeTab === tab.id
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
          {/* ==================== OVERVIEW TAB ==================== */}
          {activeTab === 'overview' && (
            <div className="space-y-10 py-4">
              {/* Basic Information */}
              <div className="relative">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-indigo-50 rounded-lg">
                    <Building2 className="h-5 w-5 text-indigo-600" />
                  </div>
                  <h3 className="text-xl font-black text-slate-900 tracking-tighter uppercase">Basic Information</h3>
                  <div className="h-px flex-1 bg-gradient-to-r from-indigo-100 to-transparent"></div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-y-8 gap-x-12 px-2">
                  <DetailItem icon={Building2} label="Organisation Name" value={organisation.name} />
                  <DetailItem
                    icon={CheckCircle}
                    label="Status"
                    value={organisation.is_active ? 'Active' : 'Inactive'}
                    color={organisation.is_active ? 'text-emerald-600' : 'text-rose-600'}
                  />
                  <DetailItem icon={Crown} label="Plan Type" value={organisation.plan_type?.charAt(0).toUpperCase() + organisation.plan_type?.slice(1)} />
                </div>
              </div>

              {/* Contact Information */}
              <div>
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <Mail className="h-5 w-5 text-blue-600" />
                  </div>
                  <h3 className="text-xl font-black text-slate-900 tracking-tighter uppercase">Contact Information</h3>
                  <div className="h-px flex-1 bg-gradient-to-r from-blue-100 to-transparent"></div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-3 gap-y-8 gap-x-12 px-2">
                  <DetailItem icon={Mail} label="Email" value={organisation.email} />
                  <DetailItem icon={Phone} label="Primary Phone" value={organisation.phone_numbers} />
                  <DetailItem icon={Phone} label="Secondary Phone" value={organisation.secondary_phone} />
                  <DetailItem icon={Globe} label="Website" value={organisation.website_url} />
                  <DetailItem icon={User} label="Admin Username" value={organisation.admin_username} />
                  <DetailItem icon={Calendar} label="Created At" value={organisation.created_at ? new Date(organisation.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : null} />
                </div>
              </div>

              {/* Address */}
              <div>
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-emerald-50 rounded-lg">
                    <MapPin className="h-5 w-5 text-emerald-600" />
                  </div>
                  <h3 className="text-xl font-black text-slate-900 tracking-tighter uppercase">Address Details</h3>
                  <div className="h-px flex-1 bg-gradient-to-r from-emerald-100 to-transparent"></div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-y-8 gap-x-12 px-2">
                  <div className="md:col-span-2">
                    <DetailItem icon={MapPin} label="Street Address" value={organisation.address} />
                  </div>
                  <DetailItem icon={MapPin} label="City" value={organisation.city} />
                  <DetailItem icon={MapPin} label="State" value={organisation.state} />
                  <DetailItem icon={Hash} label="Pincode" value={organisation.pincode} />
                </div>
              </div>

              {/* Description */}
              {organisation.description && (
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-amber-50 rounded-lg">
                      <Briefcase className="h-5 w-5 text-amber-600" />
                    </div>
                    <h3 className="text-xl font-black text-slate-900 tracking-tighter uppercase">Description</h3>
                    <div className="h-px flex-1 bg-gradient-to-r from-amber-100 to-transparent"></div>
                  </div>
                  <div className="px-2">
                    <p className="text-slate-600 font-medium leading-relaxed italic">{organisation.description}</p>
                  </div>
                </div>
              )}

              {/* Governance Notice */}
              <div className="bg-gray-50 border border-gray-200 rounded-2xl p-6 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:scale-110 transition-transform duration-500">
                  <Shield className="h-24 w-24 text-gray-400" />
                </div>
                <div className="flex items-start gap-4 relative z-10">
                  <div className="p-2 bg-indigo-100 rounded-lg">
                    <Shield className="h-6 w-6 text-indigo-600" />
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-800 text-lg tracking-tight mb-2">Governance Mode Active</h4>
                    <p className="text-gray-500 text-sm font-medium max-w-2xl leading-relaxed">
                      As Super Admin, you have full read-only visibility with critical safety controls.
                      You can manage brands and phone numbers, or inactivate the entire organisation if needed for compliance.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ==================== COMPANIES TAB ==================== */}
          {activeTab === 'companies' && (
            <div>
              <h3 className="text-lg font-bold mb-4">Companies ({companies.length})</h3>
              {companies.length === 0 ? (
                <div className="text-center py-12">
                  <Store className="h-16 w-16 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 text-lg">No companies under this organisation</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Company Name</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Contact Person</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Email</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Phone</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Brands</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Products</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {companies.map(company => (
                        <tr key={company.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <Store className="h-5 w-5 text-gray-500" />
                              <span className="font-medium">{company.name}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-gray-600">{company.contact_person || '—'}</td>
                          <td className="px-4 py-3 text-gray-600">{company.email || '—'}</td>
                          <td className="px-4 py-3 text-gray-600">{company.phone || '—'}</td>
                          <td className="px-4 py-3 text-center font-semibold">{company.brand_count || 0}</td>
                          <td className="px-4 py-3 text-center font-semibold">{company.product_count || 0}</td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-1 text-xs font-semibold rounded ${company.status === 'active'
                              ? 'bg-green-100 text-green-800'
                              : company.status === 'pending'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-gray-100 text-gray-800'
                              }`}>
                              {company.status?.charAt(0).toUpperCase() + company.status?.slice(1)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ==================== BRANDS TAB ==================== */}
          {activeTab === 'brands' && (
            <div>
              <h3 className="text-lg font-bold mb-4">Brands ({brands.length}) - View Only</h3>
              {brands.length === 0 ? (
                <div className="text-center py-12">
                  <Tag className="h-16 w-16 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 text-lg">No brands registered</p>
                </div>
              ) : (
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Brand Name</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Company Name</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Products</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {brands.map(brand => (
                      <tr key={brand.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <Tag className="h-5 w-5 text-purple-500" />
                            <span className="font-medium">{brand.name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {brand.company_name || '—'}
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

          {/* ==================== PRODUCTS TAB ==================== */}
          {activeTab === 'products' && (
            <div>
              <h3 className="text-lg font-bold mb-4">Products ({products.length}) - View Only</h3>
              {products.length === 0 ? (
                <div className="text-center py-12">
                  <Package className="h-16 w-16 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 text-lg">No products registered</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Product Name</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Brand</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Category</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Price</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {products.map(product => (
                        <tr key={product.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <Package className="h-4 w-4 text-green-500" />
                              <span className="font-medium">{product.name}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-gray-600">{product.brand_name || '—'}</td>
                          <td className="px-4 py-3 text-gray-600">{product.category || '—'}</td>
                          <td className="px-4 py-3 text-gray-600">{product.price ? `₹${product.price}` : product.price_range || '—'}</td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-1 text-xs font-semibold rounded ${product.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                              }`}>
                              {product.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ==================== PHONE NUMBERS TAB ==================== */}
          {activeTab === 'phones' && (
            <div className="space-y-8">

              {/* Company Phone Numbers */}
              <div>
                <h3 className="text-lg font-bold mb-4">Company Phone Numbers ({companies.length})</h3>
                {companies.length === 0 ? (
                  <div className="text-center py-8">
                    <Store className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">No companies under this organisation</p>
                  </div>
                ) : (
                  <table className="min-w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Company Name</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Primary No.</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Secondary No.</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {companies.map(company => (
                        <tr key={company.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <Store className="h-5 w-5 text-blue-500" />
                              <span className="font-medium">{company.name}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 font-mono text-gray-700">{company.phone || '—'}</td>
                          <td className="px-4 py-3 font-mono text-gray-700">{company.secondary_phone || '—'}</td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-1 text-xs font-semibold rounded ${company.status === 'active' ? 'bg-green-100 text-green-800' :
                              company.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                              {company.status?.charAt(0).toUpperCase() + company.status?.slice(1)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {/* ==================== TOTAL CALLS TAB ==================== */}
          {activeTab === 'calls' && (
            <div>
              <h3 className="text-lg font-bold mb-4">Total Calls ({callLogs.length})</h3>
              {callLogs.length === 0 ? (
                <div className="text-center py-12">
                  <PhoneCall className="h-16 w-16 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 text-lg">No calls recorded for this organisation</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Farmer Name</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Farmer No</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Company Name</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Duration</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Target Crop</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Recommended Product</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Status</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Satisfied</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {callLogs.map(call => (
                        <tr key={call.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium">{call.farmer_name || '—'}</td>
                          <td className="px-4 py-3 text-gray-600 font-mono text-sm">{call.farmer_phone || '—'}</td>
                          <td className="px-4 py-3 text-gray-600">{call.company_name || '—'}</td>
                          <td className="px-4 py-3 text-center text-gray-600">
                            {call.duration ? `${Math.floor(call.duration / 60)}m ${call.duration % 60}s` : '—'}
                          </td>
                          <td className="px-4 py-3 text-gray-600">{call.target_crop || '—'}</td>
                          <td className="px-4 py-3 text-gray-600">
                            {call.suggested_products && call.suggested_products.length > 0
                              ? (Array.isArray(call.suggested_products)
                                ? call.suggested_products.join(', ')
                                : call.suggested_products)
                              : '—'}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-1 text-xs font-semibold rounded ${call.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                              call.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-800' :
                                call.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                                  'bg-gray-100 text-gray-800'
                              }`}>
                              {call.status || '—'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-1 text-xs font-semibold rounded ${call.satisfaction === 'Satisfied' ? 'bg-green-100 text-green-800' :
                              call.satisfaction === 'Not Satisfied' ? 'bg-red-100 text-red-800' :
                                'bg-yellow-100 text-yellow-800'
                              }`}>
                              {call.satisfaction || 'Pending'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default OrganisationDetailView;
