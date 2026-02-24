// Organisation Platform Management - Super Admin View
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Package,
  Phone,
  PhoneCall,
  Users,
  ToggleLeft,
  ToggleRight,
  AlertTriangle,
  CheckCircle,
  Eye,
  TrendingUp
} from 'lucide-react';
import api from '../api/api';

const OrganisationsPlatformManagement = () => {
  const navigate = useNavigate();
  const [organisations, setOrganisations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [newOrgPhoneNumber, setNewOrgPhoneNumber] = useState('');
  const [newOrgDescription, setNewOrgDescription] = useState('');
  const [newOrgWebsite, setNewOrgWebsite] = useState('');
  const [newOrgPassword, setNewOrgPassword] = useState('');
  const [autoImport, setAutoImport] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchOrganisations();
  }, []);

  const fetchOrganisations = async () => {
    try {
      setLoading(true);
      const response = await api.get('/superadmin/organisations/stats');
      setOrganisations(response.data);
    } catch (error) {
      console.error('Error fetching organisations:', error);
      alert('Failed to load organisations');
    } finally {
      setLoading(false);
    }
  };

  const toggleOrganisationStatus = async (orgId, currentStatus) => {
    if (!window.confirm(
      currentStatus ? 
        'Suspend this organisation? All their services will be disabled.' : 
        'Activate this organisation? Their services will resume.'
    )) {
      return;
    }

    try {
      setProcessingId(orgId);
      await api.patch(`/superadmin/organisations/${orgId}/status`, {
        is_active: !currentStatus
      });
      
      // Update local state
      setOrganisations(orgs =>
        orgs.map(org =>
          org.id === orgId ? { ...org, is_active: !currentStatus } : org
        )
      );
    } catch (error) {
      console.error('Error toggling organisation status:', error);
      alert('Failed to update organisation status');
    } finally {
      setProcessingId(null);
    }
  };

  const handleCreateOrganisation = async () => {
    if (!newOrgName.trim()) {
      alert('Please enter organisation name');
      return;
    }
    
    if (!newOrgPhoneNumber.trim()) {
      alert('Please enter phone number for farmers to call');
      return;
    }

    setCreating(true);
    try {
      const response = await api.post('/superadmin/organisations', {
        name: newOrgName.trim(),
        primary_phone: newOrgPhoneNumber.trim(),
        description: newOrgDescription.trim() || null,
        website_url: newOrgWebsite.trim() || null,
        auto_import_products: autoImport && newOrgWebsite.trim() !== '',
        admin_password: newOrgPassword.trim() || null
      });
      
      let message = `✅ Organisation "${newOrgName}" created successfully!`;
      
      if (response.data.admin_user) {
        const admin = response.data.admin_user;
        message += `\n\n👤 Admin User Created:`;
        message += `\n📧 Username: ${admin.username}`;
        message += `\n🔑 Password: ${admin.password}`;
        message += `\n📬 Email: ${admin.email}`;
        message += `\n\n⚠️ IMPORTANT: Save these credentials! Password is shown only once.`;
      }
      
      if (response.data.import_result) {
        const result = response.data.import_result;
        message += `\n\n🎉 Auto-imported ${result.imported} products`;
        message += `\n📦 Brand created: ${result.brand_name}`;
        message += `\n🔍 Total found: ${result.total_found}`;
      }
      
      alert(message);
      
      // Close modal and reset form
      setShowCreateModal(false);
      setNewOrgName('');
      setNewOrgPhoneNumber('');
      setNewOrgDescription('');
      setNewOrgWebsite('');
      setNewOrgPassword('');
      setAutoImport(true);
      
      // Refresh list separately to avoid affecting success message
      try {
        await fetchOrganisations();
      } catch (refreshError) {
        console.error('Error refreshing organisations list:', refreshError);
        // Don't show error alert since creation was successful
      }
    } catch (error) {
      console.error('Error creating organisation:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to create organisation';
      alert(`❌ Error: ${errorMsg}`);
      
      // If organisation already exists, close modal and refresh list
      if (errorMsg.includes('already exists')) {
        setShowCreateModal(false);
        setNewOrgName('');
        setNewOrgPhoneNumber('');
        setNewOrgDescription('');
        setNewOrgWebsite('');
        setNewOrgPassword('');
        setAutoImport(true);
        
        // Refresh to show existing organisation
        try {
          await fetchOrganisations();
        } catch (refreshError) {
          console.error('Error refreshing list:', refreshError);
        }
      }
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading organisations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl shadow-lg">
            <Building2 className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Organisation Management</h1>
            <p className="text-gray-600 mt-1">Manage all platform tenants and their resources</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-all flex items-center gap-2 shadow-lg"
        >
          <Building2 className="h-5 w-5" />
          Add Organisation
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Organisations</p>
              <p className="text-3xl font-bold text-gray-900">{organisations.length}</p>
            </div>
            <Building2 className="h-10 w-10 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Active Orgs</p>
              <p className="text-3xl font-bold text-green-600">
                {organisations.filter(o => o.is_active).length}
              </p>
            </div>
            <CheckCircle className="h-10 w-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Suspended</p>
              <p className="text-3xl font-bold text-red-600">
                {organisations.filter(o => !o.is_active).length}
              </p>
            </div>
            <AlertTriangle className="h-10 w-10 text-red-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Brands</p>
              <p className="text-3xl font-bold text-purple-600">
                {organisations.reduce((sum, org) => sum + (org.brand_count || 0), 0)}
              </p>
            </div>
            <Package className="h-10 w-10 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Organisations Table */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Organisation
              </th>
              <th className="px-6 py-4 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-4 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Brands
              </th>
              <th className="px-6 py-4 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Products
              </th>
              <th className="px-6 py-4 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Phone Numbers
              </th>
              <th className="px-6 py-4 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total Calls
              </th>
              <th className="px-6 py-4 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {organisations.map((org) => (
              <tr key={org.id} className={`hover:bg-gray-50 transition-colors ${!org.is_active ? 'bg-red-50' : ''}`}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className={`flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center ${
                      org.is_active ? 'bg-blue-100' : 'bg-gray-300'
                    }`}>
                      <Building2 className={`h-5 w-5 ${org.is_active ? 'text-blue-600' : 'text-gray-600'}`} />
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{org.name}</div>
                      <div className="text-sm text-gray-500">ID: {org.id}</div>
                    </div>
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  {org.is_active ? (
                    <span className="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      Active
                    </span>
                  ) : (
                    <span className="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                      Suspended
                    </span>
                  )}
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="flex items-center justify-center gap-2">
                    <Package className="h-4 w-4 text-purple-500" />
                    <span className="text-sm font-medium text-gray-900">{org.brand_count || 0}</span>
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="flex items-center justify-center gap-2">
                    <TrendingUp className="h-4 w-4 text-green-500" />
                    <span className="text-sm font-medium text-gray-900">{org.product_count || 0}</span>
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="flex items-center justify-center gap-2">
                    <Phone className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-medium text-gray-900">{org.phone_count || 0}</span>
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="flex items-center justify-center gap-2">
                    <PhoneCall className="h-4 w-4 text-indigo-500" />
                    <span className="text-sm font-medium text-gray-900">{org.call_count || 0}</span>
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="flex items-center justify-center gap-2">
                    <button
                      onClick={() => toggleOrganisationStatus(org.id, org.is_active)}
                      disabled={processingId === org.id}
                      className={`flex items-center gap-2 px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                        org.is_active
                          ? 'bg-red-100 text-red-700 hover:bg-red-200'
                          : 'bg-green-100 text-green-700 hover:bg-green-200'
                      } ${processingId === org.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {processingId === org.id ? (
                        <>
                          <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full"></div>
                          Processing...
                        </>
                      ) : org.is_active ? (
                        <>
                          <ToggleRight className="h-4 w-4" />
                          Suspend
                        </>
                      ) : (
                        <>
                          <ToggleLeft className="h-4 w-4" />
                          Activate
                        </>
                      )}
                    </button>
                    
                    <button
                      onClick={() => navigate(`/superadmin/organisations-platform/${org.id}`)}
                      className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-200 transition-all"
                    >
                      <Eye className="h-4 w-4" />
                      View Details
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {organisations.length === 0 && (
        <div className="bg-white rounded-xl shadow-lg p-12 text-center">
          <Building2 className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">No organisations found</p>
        </div>
      )}

      {/* Create Organisation Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Building2 className="h-6 w-6 text-blue-600" />
              Add New Organisation
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Organisation Name *
                </label>
                <input
                  type="text"
                  value={newOrgName}
                  onChange={(e) => setNewOrgName(e.target.value)}
                 
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={creating}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <Phone className="h-4 w-4 text-blue-500" />
                  Phone Number (for Farmers to Call) *
                </label>
                <input
                  type="tel"
                  value={newOrgPhoneNumber}
                  onChange={(e) => setNewOrgPhoneNumber(e.target.value)}
                  
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={creating}
                />
                <p className="text-xs text-gray-500 mt-1">
                  📞 This is the number farmers will call to reach your AI assistant
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  value={newOrgDescription}
                  onChange={(e) => setNewOrgDescription(e.target.value)}
                  placeholder="Brief description about the organisation..."
                  rows={2}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={creating}
                />
              </div>

              <div>
                {/* <label className="block text-sm font-medium text-gray-700 mb-2">
                  Company Website URL (Optional)
                </label>
                <input
                  type="url"
                  value={newOrgWebsite}
                  onChange={(e) => setNewOrgWebsite(e.target.value)}
                  placeholder="https://company.com/products"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={creating}
                /> */}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                   Password 
                </label>
                <input
                  type="password"
                  value={newOrgPassword}
                  onChange={(e) => setNewOrgPassword(e.target.value)}
                  placeholder="Leave empty to auto-generate"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={creating}
               required />
                <p className="text-xs text-gray-500 mt-1">
                  If not provided, a secure random password will be generated
                </p>
              </div>

              {newOrgWebsite && (
                <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <input
                    type="checkbox"
                    id="autoImport"
                    checked={autoImport}
                    onChange={(e) => setAutoImport(e.target.checked)}
                    disabled={creating}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <label htmlFor="autoImport" className="text-sm text-blue-800 font-medium cursor-pointer">
                    🚀 Auto-import products from website
                  </label>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewOrgName('');
                    setNewOrgPhoneNumber('');
                    setNewOrgDescription('');
                    setNewOrgWebsite('');
                    setNewOrgPassword('');
                    setAutoImport(true);
                  }}
                  disabled={creating}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-all disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateOrganisation}
                  disabled={creating || !newOrgName.trim() || !newOrgPhoneNumber.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-all disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {creating ? (
                    <>
                      <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                      Creating...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      Create Organisation
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

export default OrganisationsPlatformManagement;
