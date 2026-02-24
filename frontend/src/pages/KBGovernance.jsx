import React, { useState, useEffect } from 'react';
import {
  FileText,
  CheckCircle,
  XCircle,
  Eye,
  AlertTriangle,
  Filter,
  Search,
  RefreshCw,
  Upload,
  BarChart3,
  TrendingUp,
  Clock,
  Users
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import api from '@/api/api';
import { kbUploadAPI } from '@/api/kbUploadAPI';
  
export default function KBGovernance() {
  const [kbEntries, setKbEntries] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    approved: 0,
    pending: 0,
    banned: 0
  });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);

  // Upload dialog state
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadOrgId, setUploadOrgId] = useState('');
  const [orgList, setOrgList] = useState([]);

  // Fetch orgs for admin (for org selection in upload)
  useEffect(() => {
    async function fetchOrgs() {
      try {
        const res = await api.get('/organisations?skip=0&limit=1000');
        setOrgList(res.data || []);
      } catch (e) {
        setOrgList([]);
      }
    }
    fetchOrgs();
  }, []);
  // Handle KB upload
  const handleKBUpload = async () => {
    if (!uploadFile || !uploadOrgId) {
      toast.error('Please select file and organisation');
      return;
    }
    setUploading(true);
    try {
      await kbUploadAPI.upload(uploadFile, uploadOrgId);
      toast.success('KB uploaded successfully');
      setShowUploadDialog(false);
      setUploadFile(null);
      setUploadOrgId('');
      fetchKBEntries();
    } catch (e) {
      toast.error('Upload failed: ' + (e?.response?.data?.detail || 'Unknown error'));
    } finally {
      setUploading(false);
    }
  };


  useEffect(() => {
    fetchKBEntries();
  }, []);

  const fetchKBEntries = async () => {
    try {
      setLoading(true);
      const response = await api.get('/kb/entries?limit=1000');
      
      const entries = response.data;
      setKbEntries(entries);
      
      // Calculate stats
      const stats = {
        total: entries.length,
        approved: entries.filter(e => e.is_approved && !e.is_banned).length,
        pending: entries.filter(e => !e.is_approved && !e.is_banned).length,
        banned: entries.filter(e => e.is_banned).length
      };
      setStats(stats);
      
      toast.success('KB entries loaded');
    } catch (error) {
      console.error('Error fetching KB entries:', error);
      toast.error('Failed to load KB entries');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (entryId) => {
    try {
      await api.put(
        `/kb/entries/${entryId}`,
        { is_approved: true, is_banned: false }
      );
      
      toast.success('KB entry approved');
      fetchKBEntries();
      setShowDetailDialog(false);
    } catch (error) {
      console.error('Error approving entry:', error);
      toast.error('Failed to approve entry');
    }
  };

  const handleReject = async (entryId) => {
    try {
      await api.put(
        `/kb/entries/${entryId}`,
        { is_approved: false }
      );
      
      toast.success('KB entry rejected');
      fetchKBEntries();
      setShowDetailDialog(false);
    } catch (error) {
      console.error('Error rejecting entry:', error);
      toast.error('Failed to reject entry');
    }
  };

  const handleBan = async (entryId) => {
    try {
      await api.put(
        `/kb/entries/${entryId}`,
        { is_banned: true, is_approved: false }
      );
      
      toast.success('KB entry banned');
      fetchKBEntries();
      setShowDetailDialog(false);
    } catch (error) {
      console.error('Error banning entry:', error);
      toast.error('Failed to ban entry');
    }
  };

  const handleUnban = async (entryId) => {
    try {
      await api.put(
        `/kb/entries/${entryId}`,
        { is_banned: false }
      );
      
      toast.success('KB entry unbanned');
      fetchKBEntries();
      setShowDetailDialog(false);
    } catch (error) {
      console.error('Error unbanning entry:', error);
      toast.error('Failed to unban entry');
    }
  };

  const getStatusBadge = (entry) => {
    if (entry.is_banned) {
      return <Badge variant="destructive">Banned</Badge>;
    } else if (entry.is_approved) {
      return <Badge variant="success" className="bg-green-500">Approved</Badge>;
    } else {
      return <Badge variant="warning" className="bg-yellow-500">Pending</Badge>;
    }
  };

  const filteredEntries = kbEntries.filter(entry => {
    const matchesSearch = 
      entry.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (entry.crop_name && entry.crop_name.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesFilter = 
      filterStatus === 'all' ||
      (filterStatus === 'approved' && entry.is_approved && !entry.is_banned) ||
      (filterStatus === 'pending' && !entry.is_approved && !entry.is_banned) ||
      (filterStatus === 'banned' && entry.is_banned);
    
    return matchesSearch && matchesFilter;
  });

  return (

    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Knowledge Base Governance</h1>
          <p className="text-gray-500 mt-1">Review and manage KB entries</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchKBEntries} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="default" onClick={() => setShowUploadDialog(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Add KB Data
          </Button>
        </div>
      </div>
      {/* Upload KB Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Upload Knowledge Base Data</DialogTitle>
            <DialogDescription>
              Upload a PDF or CSV file to add KB entries for a specific organisation.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Organisation</label>
              <select
                className="w-full border rounded px-3 py-2"
                value={uploadOrgId}
                onChange={e => setUploadOrgId(e.target.value)}
              >
                <option value="">Select organisation</option>
                {orgList.map(org => (
                  <option key={org.id} value={org.id}>{org.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">File (PDF or CSV)</label>
              <input
                type="file"
                accept=".pdf,.csv,application/pdf,text/csv"
                onChange={e => setUploadFile(e.target.files[0])}
                className="w-full border rounded px-3 py-2"
              />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setShowUploadDialog(false)} disabled={uploading}>Cancel</Button>
              <Button onClick={handleKBUpload} disabled={uploading || !uploadFile || !uploadOrgId}>
                {uploading ? 'Uploading...' : 'Upload'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Entries</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">All KB entries</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.approved}</div>
            <p className="text-xs text-muted-foreground">Live in system</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
            <p className="text-xs text-muted-foreground">Awaiting approval</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Banned</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.banned}</div>
            <p className="text-xs text-muted-foreground">Blocked entries</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by title, content, or crop..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Entries</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="banned">Banned</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* KB Entries Table */}
      <Card>
        <CardHeader>
          <CardTitle>Knowledge Base Entries ({filteredEntries.length})</CardTitle>
          <CardDescription>Review and manage all KB entries in the system</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400" />
              <p className="mt-4 text-gray-500">Loading entries...</p>
            </div>
          ) : filteredEntries.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 mx-auto text-gray-400" />
              <p className="mt-4 text-gray-500">No KB entries found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium">ID</th>
                    <th className="text-left py-3 px-4 font-medium">Title</th>
                    <th className="text-left py-3 px-4 font-medium">Crop</th>
                    <th className="text-left py-3 px-4 font-medium">Problem Type</th>
                    <th className="text-left py-3 px-4 font-medium">Status</th>
                    <th className="text-left py-3 px-4 font-medium">Created By</th>
                    <th className="text-left py-3 px-4 font-medium">Date</th>
                    <th className="text-left py-3 px-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEntries.map((entry) => (
                    <tr key={entry.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm">{entry.id}</td>
                      <td className="py-3 px-4">
                        <div className="font-medium text-sm">{entry.title}</div>
                        <div className="text-xs text-gray-500 truncate max-w-xs">
                          {entry.content.substring(0, 80)}...
                        </div>
                      </td>
                      <td className="py-3 px-4 text-sm">{entry.crop_name || '-'}</td>
                      <td className="py-3 px-4 text-sm">{entry.problem_type || '-'}</td>
                      <td className="py-3 px-4">{getStatusBadge(entry)}</td>
                      <td className="py-3 px-4 text-sm">{entry.created_by || 'System'}</td>
                      <td className="py-3 px-4 text-sm">
                        {new Date(entry.created_at).toLocaleDateString('en-IN')}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedEntry(entry);
                              setShowDetailDialog(true);
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {!entry.is_approved && !entry.is_banned && (
                            <Button
                              size="sm"
                              variant="default"
                              onClick={() => handleApprove(entry.id)}
                              className="bg-green-500 hover:bg-green-600"
                            >
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                          )}
                          {!entry.is_banned && (
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleBan(entry.id)}
                            >
                              <AlertTriangle className="h-4 w-4" />
                            </Button>
                          )}
                          {entry.is_banned && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleUnban(entry.id)}
                            >
                              Unban
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>KB Entry Details</DialogTitle>
            <DialogDescription>Review and manage this knowledge base entry</DialogDescription>
          </DialogHeader>
          
          {selectedEntry && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Status</label>
                <div className="mt-1">{getStatusBadge(selectedEntry)}</div>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700">Title</label>
                <p className="mt-1 text-sm text-gray-900">{selectedEntry.title}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700">Content</label>
                <p className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{selectedEntry.content}</p>
              </div>

              {selectedEntry.crop_name && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Crop Name</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedEntry.crop_name}</p>
                </div>
              )}

              {selectedEntry.problem_type && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Problem Type</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedEntry.problem_type}</p>
                </div>
              )}

              {selectedEntry.solution_steps && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Solution Steps</label>
                  <p className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                    {selectedEntry.solution_steps}
                  </p>
                </div>
              )}

              {selectedEntry.tags && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Tags</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedEntry.tags}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">Created By</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedEntry.created_by || 'System'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Language</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedEntry.language || 'hi'}</p>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700">Created At</label>
                <p className="mt-1 text-sm text-gray-900">
                  {new Date(selectedEntry.created_at).toLocaleString('en-IN')}
                </p>
              </div>
            </div>
          )}

          <DialogFooter className="flex gap-2">
            {selectedEntry && !selectedEntry.is_approved && !selectedEntry.is_banned && (
              <>
                <Button
                  variant="default"
                  onClick={() => handleApprove(selectedEntry.id)}
                  className="bg-green-500 hover:bg-green-600"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Approve
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleReject(selectedEntry.id)}
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject
                </Button>
              </>
            )}
            {selectedEntry && !selectedEntry.is_banned && (
              <Button
                variant="destructive"
                onClick={() => handleBan(selectedEntry.id)}
              >
                <AlertTriangle className="h-4 w-4 mr-2" />
                Ban Entry
              </Button>
            )}
            {selectedEntry && selectedEntry.is_banned && (
              <Button
                variant="outline"
                onClick={() => handleUnban(selectedEntry.id)}
              >
                Unban Entry
              </Button>
            )}
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
