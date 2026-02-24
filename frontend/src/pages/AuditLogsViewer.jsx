// Platform Audit Logs - Complete Compliance Tracking
import React, { useState, useEffect } from 'react';
import {
  Shield,
  Filter,
  Calendar,
  User,
  AlertCircle,
  AlertTriangle,
  Info,
  Download,
  Search,
  Building2,
  RefreshCw
} from 'lucide-react';
import api from '../api/api';

const AuditLogsViewer = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    action_category: '',
    organisation_id: '',
    severity: ''
  });
  const [organisations, setOrganisations] = useState([]);

  useEffect(() => {
    fetchLogs();
    fetchOrganisations();
  }, []);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      const response = await api.get(`/superadmin/audit-logs?${params}`);
      setLogs(response.data);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrganisations = async () => {
    try {
      const response = await api.get('/superadmin/organisations/stats');
      setOrganisations(response.data);
    } catch (error) {
      console.error('Error fetching organisations:', error);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    fetchLogs();
  };

  const resetFilters = () => {
    setFilters({
      start_date: '',
      end_date: '',
      action_category: '',
      organisation_id: '',
      severity: ''
    });
    setTimeout(() => fetchLogs(), 100);
  };

  const getSeverityBadge = (severity) => {
    const badges = {
      info: { bg: 'bg-blue-100', text: 'text-blue-800', icon: Info },
      warning: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: AlertTriangle },
      critical: { bg: 'bg-red-100', text: 'text-red-800', icon: AlertCircle }
    };
    const badge = badges[severity] || badges.info;
    const Icon = badge.icon;
    
    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${badge.bg} ${badge.text}`}>
        <Icon className="h-3 w-3" />
        {severity.toUpperCase()}
      </span>
    );
  };

  const getCategoryBadge = (category) => {
    const colors = {
      auth: 'bg-purple-100 text-purple-800',
      organisation: 'bg-blue-100 text-blue-800',
      product: 'bg-green-100 text-green-800',
      config: 'bg-red-100 text-red-800',
      kb: 'bg-yellow-100 text-yellow-800',
      user: 'bg-pink-100 text-pink-800'
    };
    
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${colors[category] || 'bg-gray-100 text-gray-800'}`}>
        {category}
      </span>
    );
  };

  const exportToCSV = () => {
    const headers = ['Timestamp', 'User', 'Action', 'Category', 'Entity', 'Severity', 'IP Address'];
    const rows = logs.map(log => [
      new Date(log.timestamp).toLocaleString(),
      `${log.user?.name || 'System'} (${log.user?.email || 'N/A'})`,
      log.action_type,
      log.action_category,
      log.entity_id || 'N/A',
      log.severity,
      log.ip_address || 'N/A'
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-gray-700 to-gray-900 rounded-xl shadow-lg">
            <Shield className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
            <p className="text-gray-600 mt-1">Complete platform activity tracking & compliance</p>
          </div>
        </div>
        
        <button
          onClick={exportToCSV}
          disabled={logs.length === 0}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Download className="h-4 w-4" />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex items-center gap-3 mb-4">
          <Filter className="h-5 w-5 text-gray-600" />
          <h2 className="text-lg font-bold text-gray-900">Filters</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
            <select
              value={filters.action_category}
              onChange={(e) => handleFilterChange('action_category', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="">All Categories</option>
              <option value="auth">Authentication</option>
              <option value="organisation">Organisation</option>
              <option value="product">Product</option>
              <option value="config">Configuration</option>
              <option value="kb">Knowledge Base</option>
              <option value="user">User Management</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Organisation</label>
            <select
              value={filters.organisation_id}
              onChange={(e) => handleFilterChange('organisation_id', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="">All Organisations</option>
              {organisations.map(org => (
                <option key={org.id} value={org.id}>{org.name}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Severity</label>
            <select
              value={filters.severity}
              onChange={(e) => handleFilterChange('severity', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="">All Severities</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
            </select>
          </div>
        </div>
        
        <div className="flex gap-3 mt-4">
          <button
            onClick={applyFilters}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all"
          >
            <Search className="h-4 w-4" />
            Apply Filters
          </button>
          <button
            onClick={resetFilters}
            className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-all"
          >
            <RefreshCw className="h-4 w-4" />
            Reset
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center p-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-indigo-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading audit logs...</p>
            </div>
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center">
            <Shield className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">No audit logs found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                  <th className="px-6 py-4 text-center text-xs font-medium text-gray-500 uppercase">Category</th>
                  <th className="px-6 py-4 text-center text-xs font-medium text-gray-500 uppercase">Severity</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        <div className="text-sm text-gray-900">
                          {new Date(log.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-gray-400" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {log.user?.name || 'System'}
                          </div>
                          <div className="text-xs text-gray-500">{log.user?.email || 'N/A'}</div>
                        </div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 font-medium">{log.action_type}</div>
                      {log.entity_id && (
                        <div className="text-xs text-gray-500">Entity: {log.entity_id}</div>
                      )}
                    </td>
                    
                    <td className="px-6 py-4 text-center">
                      {getCategoryBadge(log.action_category)}
                    </td>
                    
                    <td className="px-6 py-4 text-center">
                      {getSeverityBadge(log.severity)}
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 font-mono">{log.ip_address || 'N/A'}</div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Total Count */}
      {logs.length > 0 && (
        <div className="text-center text-gray-600">
          Showing {logs.length} audit log(s)
        </div>
      )}
    </div>
  );
};

export default AuditLogsViewer;
