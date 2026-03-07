// Superadmin Call Logs - Platform-wide Communication Tracking
import React, { useState, useEffect } from 'react';
import {
  Phone,
  Search,
  Calendar as CalendarIcon,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Building2,
  Filter,
  RefreshCw,
  Download,
  Building
} from 'lucide-react';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import api from '@/api/api';

const SuperAdminCallLogs = () => {
  const [logs, setLogs] = useState([]);
  const [organisations, setOrganisations] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const [filters, setFilters] = useState({
    startDate: (() => {
      const d = new Date();
      d.setDate(d.getDate() - 7);
      return d.toISOString().split('T')[0];
    })(),
    endDate: new Date().toISOString().split('T')[0],
    organisationId: 'ALL',
    companyId: 'ALL',
    farmerSearch: ''
  });

  useEffect(() => {
    fetchOrganisations();
    fetchCallLogs();
  }, []);

  useEffect(() => {
    if (filters.organisationId !== 'ALL') {
      fetchCompanies(filters.organisationId);
    } else {
      setCompanies([]);
      setFilters(prev => ({ ...prev, companyId: 'ALL' }));
    }
  }, [filters.organisationId]);

  const fetchOrganisations = async () => {
    try {
      const response = await api.get('/superadmin/organisations/stats');
      setOrganisations(response.data || []);
    } catch (error) {
      console.error('Error fetching organisations:', error);
    }
  };

  const fetchCompanies = async (orgId) => {
    try {
      if (!orgId || orgId === 'ALL') {
        setCompanies([]);
        return;
      }
      const response = await api.get(`/admin/companies?organisation_id=${orgId}`);
      setCompanies(response.data || []);
    } catch (error) {
      console.error('Error fetching companies:', error);
      setCompanies([]);
    }
  };

  const fetchCallLogs = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filters.startDate) params.start_date = new Date(filters.startDate).toISOString();
      if (filters.endDate) {
        const end = new Date(filters.endDate);
        end.setHours(23, 59, 59, 999);
        params.end_date = end.toISOString();
      }
      if (filters.organisationId && filters.organisationId !== 'ALL') {
        params.organisation_id = filters.organisationId;
      }
      if (filters.companyId && filters.companyId !== 'ALL') {
        params.company_id = filters.companyId;
      }

      const response = await api.get('/superadmin/calls', { params });
      setLogs(response.data || []);
    } catch (error) {
      console.error('Error fetching call logs:', error);
      toast.error('Failed to load call history');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => {
      const newFilters = { ...prev, [key]: value };
      if (key === 'organisationId') {
        newFilters.companyId = 'ALL';
      }
      return newFilters;
    });
  };

  const applyFilters = (e) => {
    if (e) e.preventDefault();
    fetchCallLogs();
  };

  const resetFilters = () => {
    setFilters({
      startDate: (() => {
        const d = new Date();
        d.setDate(d.getDate() - 7);
        return d.toISOString().split('T')[0];
      })(),
      endDate: new Date().toISOString().split('T')[0],
      organisationId: 'ALL',
      companyId: 'ALL',
      farmerSearch: ''
    });
    setSearchQuery('');
    setTimeout(() => fetchCallLogs(), 100);
  };

  const filteredLogs = logs.filter(log => {
    const searchLow = searchQuery.toLowerCase();
    const farmerSearchLow = filters.farmerSearch.toLowerCase();

    const matchesGlobalSearch = searchQuery === '' ||
      log.farmer_phone?.includes(searchQuery) ||
      log.farmer_name?.toLowerCase().includes(searchLow) ||
      log.organisation_name?.toLowerCase().includes(searchLow) ||
      log.company_name?.toLowerCase().includes(searchLow) ||
      log.target_crop?.toLowerCase().includes(searchLow);

    const matchesFarmerSearch = filters.farmerSearch === '' ||
      log.farmer_phone?.includes(filters.farmerSearch) ||
      log.farmer_name?.toLowerCase().includes(farmerSearchLow);

    return matchesGlobalSearch && matchesFarmerSearch;
  });

  const formatDuration = (seconds) => {
    if (!seconds) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusBadge = (status) => {
    switch (status?.toUpperCase()) {
      case 'COMPLETED':
        return <Badge className="bg-green-100 text-green-800 border-green-200">Completed</Badge>;
      case 'FAILED':
        return <Badge className="bg-red-100 text-red-800 border-red-200">Failed</Badge>;
      case 'ACTIVE':
        return <Badge className="bg-blue-100 text-blue-800 border-blue-200">Active</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getSatisfactionStatusIcon = (satisfaction) => {
    if (satisfaction === 'Satisfied') return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    if (satisfaction === 'Not Satisfied') return <XCircle className="h-5 w-5 text-red-500" />;
    return <AlertCircle className="h-5 w-5 text-gray-400" />; // Pending or Unknown
  };

  const exportToCSV = () => {
    const headers = ['Timestamp', 'Farmer Name', 'Farmer Phone', 'Organisation', 'Company', 'Duration', 'Target Crop', 'Status', 'Satisfied'];
    const rows = filteredLogs.map(log => [
      log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A',
      log.farmer_name || 'Unknown',
      log.farmer_phone || 'N/A',
      log.organisation_name || 'N/A',
      log.company_name || 'N/A',
      formatDuration(log.duration),
      log.target_crop || 'N/A',
      log.status || 'N/A',
      log.satisfaction || 'Pending'
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `call_logs_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Phone className="h-8 w-8 text-primary" />
            Call Logs
          </h1>
          <Badge variant="secondary" className="mt-1 bg-purple-100 text-purple-700">{logs.length} Total Calls</Badge>
        </div>

        <button
          onClick={exportToCSV}
          disabled={filteredLogs.length === 0}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Download className="h-4 w-4" />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <Card className="border-gray-200 shadow-sm">
        <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2 bg-gray-50/50 rounded-t-xl">
          <Filter className="w-4 h-4 text-gray-500" />
          <h2 className="font-semibold text-gray-700 text-sm">Filters</h2>
        </div>
        <CardContent className="p-4">
          <form onSubmit={applyFilters} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4 items-end">
            <div className="grid gap-1.5">
              <Label className="text-xs text-gray-500 font-medium">Start Date</Label>
              <div className="relative">
                <CalendarIcon className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
                <Input type="date" value={filters.startDate} onChange={(e) => handleFilterChange('startDate', e.target.value)} className="pl-9 h-9 text-sm" />
              </div>
            </div>

            <div className="grid gap-1.5">
              <Label className="text-xs text-gray-500 font-medium">End Date</Label>
              <div className="relative">
                <CalendarIcon className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
                <Input type="date" value={filters.endDate} onChange={(e) => handleFilterChange('endDate', e.target.value)} className="pl-9 h-9 text-sm" />
              </div>
            </div>

            <div className="grid gap-1.5">
              <Label className="text-xs text-gray-500 font-medium">Organisation</Label>
              <Select value={filters.organisationId} onValueChange={(v) => handleFilterChange('organisationId', v)}>
                <SelectTrigger className="h-9 text-sm">
                  <SelectValue placeholder="All Organisations" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Organisations</SelectItem>
                  {organisations.map((org) => (
                    <SelectItem key={org.id} value={org.id.toString()}>{org.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-1.5">
              <Label className="text-xs text-gray-500 font-medium">Company</Label>
              <Select
                value={filters.companyId}
                onValueChange={(v) => handleFilterChange('companyId', v)}
                disabled={filters.organisationId === 'ALL'}
              >
                <SelectTrigger className="h-9 text-sm">
                  <SelectValue placeholder={filters.organisationId === 'ALL' ? "Select Org First" : "All Companies"} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Companies</SelectItem>
                  {companies.map((company) => (
                    <SelectItem key={company.id} value={company.id.toString()}>{company.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-1.5">
              <Label className="text-xs text-gray-500 font-medium">Farmer Name / Phone</Label>
              <Input
                placeholder="Search farmer..."
                value={filters.farmerSearch}
                onChange={(e) => handleFilterChange('farmerSearch', e.target.value)}
                className="h-9 text-sm"
              />
            </div>

            <div className="flex gap-2 lg:col-span-2">
              <Button type="submit" className="flex-1 h-9 bg-indigo-600 hover:bg-indigo-700 text-white">
                <Search className="w-4 h-4 mr-2" />
                Apply
              </Button>
              <Button type="button" variant="outline" onClick={resetFilters} className="flex-1 h-9 bg-gray-100 text-gray-700 hover:bg-gray-200 border-none">
                <RefreshCw className="w-4 h-4 mr-2" />
                Reset
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card className="border border-gray-200 shadow-lg overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex flex-col sm:flex-row justify-between items-center gap-4 bg-gray-50/50">
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search by phone, company, crop..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-white"
            />
          </div>
          <div className="text-sm font-medium text-gray-500">
            {filteredLogs.length} call records found
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 border-b border-gray-200 text-gray-700">
              <tr>
                <th className="px-6 py-4 font-semibold whitespace-nowrap">Farmer Name</th>
                <th className="px-6 py-4 font-semibold whitespace-nowrap">Farmer Phone</th>
                <th className="px-6 py-4 font-semibold whitespace-nowrap">Organisation</th>
                <th className="px-6 py-4 font-semibold whitespace-nowrap">Company</th>
                <th className="px-6 py-4 font-semibold whitespace-nowrap">Duration</th>
                <th className="px-6 py-4 font-semibold whitespace-nowrap">Target Crop</th>
                <th className="px-6 py-4 font-semibold">Recommended Product</th>
                <th className="px-6 py-4 font-semibold whitespace-nowrap">Status</th>
                <th className="px-6 py-4 font-semibold whitespace-nowrap text-center">Satisfied</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {loading ? (
                <tr>
                  <td colSpan="9" className="px-6 py-12 text-center text-gray-500">
                    <div className="flex flex-col items-center justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4"></div>
                      <p>Loading call history...</p>
                    </div>
                  </td>
                </tr>
              ) : filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan="9" className="px-6 py-12 text-center text-gray-500">
                    <Phone className="mx-auto h-12 w-12 text-gray-300 mb-3" />
                    <p className="text-lg font-medium text-gray-900">No calls found</p>
                    <p className="text-sm">Try adjusting your filters or search query.</p>
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold">
                          {log.farmer_name ? log.farmer_name.charAt(0).toUpperCase() : 'U'}
                        </div>
                        <span className="font-medium text-gray-900">{log.farmer_name || 'Unknown Farmer'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 text-gray-400" />
                        <span className="font-medium font-mono text-gray-700">{log.farmer_phone}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Building className="h-4 w-4 text-gray-400" />
                        <span className="font-medium text-gray-700">{log.organisation_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-gray-400" />
                        <span className="font-medium text-gray-700">{log.company_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-1.5 text-gray-600">
                        <Clock className="h-4 w-4" />
                        <span>{formatDuration(log.duration)}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">
                      {log.target_crop || "Not Identified"}
                    </td>
                    <td className="px-6 py-4">
                      <div className="max-w-md">
                        {log.suggested_products && log.suggested_products.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-2">
                            {log.suggested_products.map((p, i) => (
                              <Badge key={i} variant="secondary" className="bg-purple-50 text-purple-700 border-purple-200 text-xs">
                                {p}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {log.key_recommendations && log.key_recommendations.length > 0 ? (
                          <p className="text-xs text-gray-600 line-clamp-2" title={log.key_recommendations.join(', ')}>
                            {log.key_recommendations[0]} {log.key_recommendations.length > 1 && '...'}
                          </p>
                        ) : (
                          <p className="text-xs text-gray-400 italic">No recommendations</p>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(log.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <div className="flex justify-center" title={`Status: ${log.satisfaction || 'Pending'}`}>
                        {getSatisfactionStatusIcon(log.satisfaction)}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {logs.length > 0 && (
          <div className="p-4 border-t border-gray-100 text-center text-gray-500 text-sm">
            Showing {filteredLogs.length} call record(s)
          </div>
        )}
      </Card>
    </div>
  );
};

export default SuperAdminCallLogs;
