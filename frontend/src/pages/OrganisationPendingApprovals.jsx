import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from 'sonner';
import { Clock, CheckCircle, XCircle, Building2, User, Mail, Calendar, Eye, UserPlus, Ban, UserCheck } from 'lucide-react';
import api from '@/api/api';

export default function OrganisationPendingApprovals() {
  const [loading, setLoading] = useState(true);
  const [approvals, setApprovals] = useState([]);
  const [todayRegistrations, setTodayRegistrations] = useState([]);
  const [todayRejections, setTodayRejections] = useState([]);
  const [processing, setProcessing] = useState({});
  const [stats, setStats] = useState({
    pending_count: 0,
    approved_count: 0,
    rejected_count: 0,
    today_registrations: 0,
    today_rejections: 0,
    total_company_users: 0
  });

  useEffect(() => {
    fetchPendingApprovals();
    fetchApprovalStats();
    fetchTodayRegistrations();
    fetchTodayRejections();
  }, []);

  const fetchPendingApprovals = async () => {
    try {
      setLoading(true);
      const response = await api.get('/organisation/pending-approvals');
      setApprovals(response.data.pending_approvals || []);
    } catch (error) {
      console.error('Error fetching pending approvals:', error);
      toast.error('Failed to load pending approvals');
    } finally {
      setLoading(false);
    }
  };

  const fetchApprovalStats = async () => {
    try {
      const response = await api.get('/organisation/approval-stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching approval stats:', error);
      toast.error('Failed to load approval statistics');
    }
  };

  const fetchTodayRegistrations = async () => {
    try {
      const response = await api.get('/organisation/today-registrations');
      setTodayRegistrations(response.data.today_registrations || []);
    } catch (error) {
      console.error('Error fetching today registrations:', error);
      toast.error('Failed to load today registrations');
    }
  };

  const fetchTodayRejections = async () => {
    try {
      const response = await api.get('/organisation/today-rejections');
      setTodayRejections(response.data.today_rejections || []);
    } catch (error) {
      console.error('Error fetching today rejections:', error);
      toast.error('Failed to load today rejections');
    }
  };

  const handleApprove = async (userId) => {
    try {
      setProcessing(prev => ({ ...prev, [userId]: true }));

      await api.post(`/organisation/approve-user/${userId}`);

      // Update local state
      setApprovals(prev => prev.filter(item => item.id !== userId));

      // Refresh stats
      await fetchApprovalStats();
      await fetchTodayRegistrations();
      await fetchTodayRejections();

      toast.success('User approved successfully!');
    } catch (error) {
      console.error('Error approving user:', error);
      toast.error('Failed to approve user');
    } finally {
      setProcessing(prev => ({ ...prev, [userId]: false }));
    }
  };

  const handleReject = async (userId) => {
    try {
      setProcessing(prev => ({ ...prev, [userId]: true }));

      await api.post(`/organisation/reject-user/${userId}`);

      // Update local state
      setApprovals(prev => prev.filter(item => item.id !== userId));

      // Refresh stats
      await fetchApprovalStats();
      await fetchTodayRegistrations();
      await fetchTodayRejections();

      toast.success('User rejected successfully!');
    } catch (error) {
      console.error('Error rejecting user:', error);
      toast.error('Failed to reject user');
    } finally {
      setProcessing(prev => ({ ...prev, [userId]: false }));
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusBadge = (status, isActive) => {
    if (status === 'active' && isActive) {
      return (
        <Badge variant="secondary" className="bg-green-100 text-green-800">
          <CheckCircle className="h-3 w-3 mr-1" />
          Approved
        </Badge>
      );
    }
    if (status === 'inactive') {
      return (
        <Badge variant="secondary" className="bg-gray-100 text-gray-800">
          <Ban className="h-3 w-3 mr-1" />
          Inactive
        </Badge>
      );
    }
    if (status === 'rejected') {
      return (
        <Badge variant="secondary" className="bg-red-100 text-red-800">
          <XCircle className="h-3 w-3 mr-1" />
          Rejected
        </Badge>
      );
    }
    return (
      <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
        <Clock className="h-3 w-3 mr-1" />
        Pending
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading pending approvals...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <UserCheck className="h-8 w-8 text-primary" />
          Pending Approvals
        </h1>
        <p className="text-muted-foreground mt-1">
          Review and approve company user registration requests
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pending_count}</div>
            <p className="text-xs text-muted-foreground">Awaiting approval</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.approved_count}</div>
            <p className="text-xs text-muted-foreground">Total approved</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rejected</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.rejected_count}</div>
            <p className="text-xs text-muted-foreground">Total rejected</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.today_registrations}</div>
            <p className="text-xs text-muted-foreground">New registrations</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_company_users}</div>
            <p className="text-xs text-muted-foreground">All company users</p>
          </CardContent>
        </Card>
      </div>

      {/* Pending Approvals Table */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Company User Registration Requests
          </CardTitle>
          <CardDescription>
            Review details and approve or reject pending company user registrations
          </CardDescription>
        </CardHeader>
        <CardContent>
          {approvals.length === 0 ? (
            <div className="text-center py-8">
              <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Pending Approvals</h3>
              <p className="text-muted-foreground">All company user registrations have been reviewed.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User Details</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Registration Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {approvals.map((approval) => (
                  <TableRow key={approval.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="font-bold text-gray-900">
                            {approval.full_name || approval.username}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Mail className="h-3 w-3" />
                          <span>{approval.email}</span>
                        </div>
                        {approval.full_name && (
                          <div className="text-xs text-muted-foreground ml-6">
                            @{approval.username}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-gray-900">{approval.company_name}</div>
                        <Badge variant="outline" className="text-[10px] uppercase tracking-wider font-bold bg-gray-50">
                          {approval.role.replace('_', ' ')}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {formatDate(approval.created_at)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                        <Clock className="h-3 w-3 mr-1" />
                        Pending
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          onClick={() => handleApprove(approval.id)}
                          disabled={processing[approval.id]}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          {processing[approval.id] ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          ) : (
                            <>
                              <CheckCircle className="h-4 w-4 mr-1" />
                              Approve
                            </>
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleReject(approval.id)}
                          disabled={processing[approval.id]}
                        >
                          {processing[approval.id] ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          ) : (
                            <>
                              <XCircle className="h-4 w-4 mr-1" />
                              Reject
                            </>
                          )}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>


      {/* Today's New Registrations Table */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5 text-blue-600" />
            Today's New Registrations
          </CardTitle>
          <CardDescription>
            All company admin registrations received today
          </CardDescription>
        </CardHeader>
        <CardContent>
          {todayRegistrations.length === 0 ? (
            <div className="text-center py-8">
              <UserPlus className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Registrations Today</h3>
              <p className="text-muted-foreground">No new company registrations have been received today.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User Details</TableHead>
                  <TableHead>Companies</TableHead>
                  <TableHead>Registration Time</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {todayRegistrations.map((reg) => (
                  <TableRow key={reg.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="font-bold text-gray-900">
                            {reg.full_name || reg.username}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Mail className="h-3 w-3" />
                          <span>{reg.email}</span>
                        </div>
                        {reg.full_name && (
                          <div className="text-xs text-muted-foreground ml-6">
                            @{reg.username}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-gray-900">{reg.company_name}</div>
                        <Badge variant="outline" className="text-[10px] uppercase tracking-wider font-bold bg-gray-50">
                          {reg.role.replace('_', ' ')}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {formatDate(reg.created_at)}
                      </div>
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(reg.company_status, reg.is_active)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Today's Rejected Users Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Ban className="h-5 w-5 text-red-600" />
            Today's Rejected Users
          </CardTitle>
          <CardDescription>
            Company registrations rejected today
          </CardDescription>
        </CardHeader>
        <CardContent>
          {todayRejections.length === 0 ? (
            <div className="text-center py-8">
              <Ban className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Rejections Today</h3>
              <p className="text-muted-foreground">No company registrations have been rejected today.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User Details</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Registration Date</TableHead>
                  <TableHead>Rejected At</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {todayRejections.map((rej) => (
                  <TableRow key={rej.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="font-bold text-gray-900">
                            {rej.full_name || rej.username}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Mail className="h-3 w-3" />
                          <span>{rej.email}</span>
                        </div>
                        {rej.full_name && (
                          <div className="text-xs text-muted-foreground ml-6">
                            @{rej.username}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{rej.company_name}</div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {formatDate(rej.created_at)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {rej.rejected_at ? formatDate(rej.rejected_at) : '—'}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="bg-red-100 text-red-800">
                        <XCircle className="h-3 w-3 mr-1" />
                        Rejected
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
