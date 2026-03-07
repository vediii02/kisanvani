import React, { useState, useEffect } from 'react';
import { Phone, Search, Calendar as CalendarIcon, Clock, CheckCircle2, XCircle, AlertCircle, Building2, Filter, RefreshCw } from 'lucide-react';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import api from '@/api/api';

export default function OrganisationCallLogs() {
    const [logs, setLogs] = useState([]);
    const [companies, setCompanies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterCompanyId, setFilterCompanyId] = useState('');

    const [dateFilter, setDateFilter] = useState('week');
    const [farmerSearch, setFarmerSearch] = useState('');

    const [startDate, setStartDate] = useState(() => {
        const d = new Date();
        d.setDate(d.getDate() - 7);
        return d.toISOString().split('T')[0];
    });

    const [endDate, setEndDate] = useState(() => {
        const d = new Date();
        return d.toISOString().split('T')[0];
    });

    useEffect(() => {
        const today = new Date();
        if (dateFilter === 'today') {
            const d = today.toISOString().split('T')[0];
            setStartDate(d);
            setEndDate(d);
        } else if (dateFilter === 'week') {
            const dStart = new Date();
            dStart.setDate(dStart.getDate() - 7);
            setStartDate(dStart.toISOString().split('T')[0]);
            setEndDate(today.toISOString().split('T')[0]);
        } else if (dateFilter === 'month') {
            const start = new Date(today.getFullYear(), today.getMonth(), 1);
            setStartDate(start.toISOString().split('T')[0]);
            setEndDate(today.toISOString().split('T')[0]);
        }
    }, [dateFilter]);

    useEffect(() => {
        fetchCompanies();
    }, []);

    useEffect(() => {
        fetchCallLogs();
    }, [startDate, endDate, filterCompanyId]);

    const fetchCompanies = async () => {
        try {
            const response = await api.get('/organisation/companies');
            // Some endpoints return { companies: [...] } while others return direct arrays
            setCompanies(response.data.companies || response.data || []);
        } catch (error) {
            console.error('Error fetching companies:', error);
            toast.error('Failed to load companies for filter');
        }
    };

    const fetchCallLogs = async () => {
        try {
            setLoading(true);
            const params = {};
            if (startDate) params.start_date = new Date(startDate).toISOString();
            if (endDate) {
                const end = new Date(endDate);
                end.setHours(23, 59, 59, 999);
                params.end_date = end.toISOString();
            }
            if (filterCompanyId && filterCompanyId !== 'ALL') {
                params.filter_company_id = filterCompanyId;
            }

            const response = await api.get('/company/calls', { params });
            setLogs(response.data || []);
        } catch (error) {
            console.error('Error fetching call logs:', error);
            toast.error('Failed to load call history');
        } finally {
            setLoading(false);
        }
    };

    const handleApplyFilter = (e) => {
        e.preventDefault();
        fetchCallLogs();
    };

    const handleReset = () => {
        setDateFilter('week');
        setFilterCompanyId('ALL');
        setFarmerSearch('');
        setSearchQuery('');
    };

    const filteredLogs = logs.filter(log =>
        (farmerSearch === '' ||
            log.farmer_phone?.includes(farmerSearch) ||
            log.farmer_name?.toLowerCase().includes(farmerSearch.toLowerCase())) &&
        (log.farmer_phone?.includes(searchQuery) ||
            log.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            log.target_crop?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (Array.isArray(log.suggested_products) && log.suggested_products.some(p => String(p).toLowerCase().includes(searchQuery.toLowerCase()))) ||
            (Array.isArray(log.key_recommendations) && log.key_recommendations.some(r => String(r).toLowerCase().includes(searchQuery.toLowerCase()))))
    );

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

    return (
        <div className="container mx-auto py-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                <div className="flex items-center gap-3">
                    <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                        <Phone className="w-8 h-8 text-primary" />
                        Call Logs
                    </h1>
                    <Badge variant="secondary" className="mt-1 bg-purple-100 text-purple-700">{logs.length} Total Calls</Badge>
                </div>
            </div>

            {/* Filter Section matching screenshot */}
            <Card className="mb-6 border-gray-200 shadow-sm">
                <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2 bg-gray-50/50 rounded-t-xl">
                    <Filter className="w-4 h-4 text-gray-500" />
                    <h2 className="font-semibold text-gray-700 text-sm">Filters</h2>
                </div>
                <CardContent className="p-4">
                    <form onSubmit={handleApplyFilter} className="flex flex-wrap items-end gap-4">

                        {/* Time Period */}
                        <div className="grid gap-1.5 flex-1 min-w-[150px]">
                            <Label className="text-xs text-gray-500 font-medium">Time Period</Label>
                            <Select value={dateFilter} onValueChange={setDateFilter}>
                                <SelectTrigger className="h-9 text-sm">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="today">Today</SelectItem>
                                    <SelectItem value="week">This Week</SelectItem>
                                    <SelectItem value="month">This Month</SelectItem>
                                    <SelectItem value="custom">Custom Range</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Dates */}
                        <div className="grid gap-1.5 flex-1 min-w-[140px]">
                            <Label className="text-xs text-gray-500 font-medium">Start Date</Label>
                            <div className="relative">
                                <CalendarIcon className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
                                <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="pl-9 h-9 text-sm" />
                            </div>
                        </div>
                        <div className="grid gap-1.5 flex-1 min-w-[140px]">
                            <Label className="text-xs text-gray-500 font-medium">End Date</Label>
                            <div className="relative">
                                <CalendarIcon className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
                                <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="pl-9 h-9 text-sm" />
                            </div>
                        </div>

                        {/* Farmer Search */}
                        <div className="grid gap-1.5 flex-1 min-w-[180px]">
                            <Label className="text-xs text-gray-500 font-medium">Farmer Name / Phone</Label>
                            <Input
                                placeholder="Search farmer..."
                                value={farmerSearch}
                                onChange={(e) => setFarmerSearch(e.target.value)}
                                className="h-9 text-sm"
                            />
                        </div>

                        {/* Organisation/Company */}
                        <div className="grid gap-1.5 flex-1 min-w-[200px]">
                            <Label className="text-xs text-gray-500 font-medium">Company</Label>
                            <Select value={filterCompanyId} onValueChange={setFilterCompanyId}>
                                <SelectTrigger className="h-9 text-sm">
                                    <SelectValue placeholder="All Companies" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="ALL">All Companies</SelectItem>
                                    {companies.map((c) => (
                                        <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2 w-full sm:w-auto mt-2 sm:mt-0">
                            <Button type="submit" className="h-9 w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700 text-white">
                                <Search className="w-4 h-4 mr-2" />
                                Apply Filters
                            </Button>
                            <Button type="button" variant="secondary" onClick={handleReset} className="h-9 w-full sm:w-auto bg-gray-100 text-gray-700 hover:bg-gray-200">
                                <RefreshCw className="w-4 h-4 mr-2" />
                                Reset
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>

            <Card className="border border-gray-200 shadow-sm">
                <CardContent className="p-0">
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
                                        <td colSpan="8" className="px-6 py-12 text-center text-gray-500">
                                            <div className="flex flex-col items-center justify-center">
                                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mb-4"></div>
                                                <p>Loading call history...</p>
                                            </div>
                                        </td>
                                    </tr>
                                ) : filteredLogs.length === 0 ? (
                                    <tr>
                                        <td colSpan="8" className="px-6 py-12 text-center text-gray-500">
                                            <Phone className="mx-auto h-12 w-12 text-gray-300 mb-3" />
                                            <p className="text-lg font-medium text-gray-900">No calls found</p>
                                            <p className="text-sm">Try adjusting your date/company filters or search query.</p>
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
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="font-medium text-gray-900">
                                                    {log.target_crop || "Not Identified"}
                                                </div>
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
                </CardContent>
            </Card>
        </div>
    );
}
