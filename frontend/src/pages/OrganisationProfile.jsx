// Organisation Profile Management
import React, { useState, useEffect } from 'react';
import { Building2, Phone, Mail, Globe, Save, AlertCircle, CheckCircle, X } from 'lucide-react';
import api from '../api/api';

const OrganisationProfile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    phone: '',
    email: '',
    description: '',
    is_active: true
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const response = await api.get('/org-admin/profile');
      setProfile(response.data);
      setFormData({
        name: response.data.name || '',
        domain: response.data.domain || '',
        phone: response.data.phone || '',
        email: response.data.email || '',
        description: response.data.description || '',
        is_active: response.data.is_active
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError('');
      setSuccess('');
      
      const response = await api.put('/org-admin/profile', formData);
      setProfile(response.data);
      setSuccess('Profile updated successfully!');
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Organisation Profile</h1>
        <p className="text-gray-600 mt-1">Manage your organisation information</p>
      </div>

      {/* Alerts */}
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

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start">
          <CheckCircle className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-green-800 font-medium">Success</h3>
            <p className="text-green-600 text-sm mt-1">{success}</p>
          </div>
          <button onClick={() => setSuccess('')} className="text-green-600 hover:text-green-700">
            <X className="h-5 w-5" />
          </button>
        </div>
      )}

      {/* Profile Information Card */}
      {profile && (
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center gap-4 mb-4">
            <div className="bg-white bg-opacity-20 p-4 rounded-lg">
              <Building2 className="h-8 w-8" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">{profile.name}</h2>
              <div className="flex items-center gap-2 mt-1">
                {profile.is_enterprise && (
                  <span className="px-2 py-1 bg-yellow-400 text-yellow-900 text-xs font-bold rounded">
                    ENTERPRISE
                  </span>
                )}
                <span className={`px-2 py-1 text-xs font-semibold rounded ${
                  profile.is_active 
                    ? 'bg-green-400 text-green-900' 
                    : 'bg-red-400 text-red-900'
                }`}>
                  {profile.is_active ? 'ACTIVE' : 'INACTIVE'}
                </span>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
            {profile.domain && (
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4" />
                <span className="text-sm">{profile.domain}</span>
              </div>
            )}
            {profile.phone && (
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4" />
                <span className="text-sm">{profile.phone}</span>
              </div>
            )}
            {profile.email && (
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                <span className="text-sm">{profile.email}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Edit Form */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Edit Profile Information</h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Organisation Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Domain
              </label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={formData.domain}
                  onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="example.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Phone Number
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="+91 1234567890"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="contact@example.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="Tell us about your organisation..."
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
              Organisation is active
            </label>
          </div>

          <div className="flex gap-4 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={fetchProfile}
              disabled={saving}
              className="flex-1 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium disabled:opacity-50"
            >
              Reset
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium disabled:opacity-50"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-5 w-5" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Additional Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <AlertCircle className="h-5 w-5 text-blue-600" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Important Information</h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Changes to your organisation profile may take a few moments to reflect</li>
                <li>Contact your super admin if you need to modify enterprise status</li>
                <li>Ensure your contact information is always up to date</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrganisationProfile;
