import React, { useState } from 'react';
import { ingestAPI } from '@/api/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, Trash2, FileText, AlertCircle, CheckCircle } from 'lucide-react';

export default function DocumentManagement({ companyId }) {
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setMessage('');
    
    try {
      const response = await ingestAPI.uploadDocument(companyId, file);
      setMessage(`Document "${file.name}" uploaded and ingested successfully!`);
      setMessageType('success');
      event.target.value = ''; // Clear file input
    } catch (error) {
      console.error('Upload error:', error);
      setMessage(error.response?.data?.detail || 'Failed to upload document');
      setMessageType('error');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteData = async () => {
    if (!window.confirm('Are you sure you want to delete all knowledge base data for this company? This action cannot be undone.')) {
      return;
    }

    setDeleting(true);
    setMessage('');
    
    try {
      const response = await ingestAPI.deleteCompanyData(companyId);
      setMessage(response.data.message || 'Company data deleted successfully!');
      setMessageType('success');
    } catch (error) {
      console.error('Delete error:', error);
      setMessage(error.response?.data?.detail || 'Failed to delete company data');
      setMessageType('error');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Card className="p-6 border border-border/60">
      <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <FileText className="w-5 h-5" />
        Document Management
      </h3>
      
      <div className="space-y-4">
        {/* Upload Section */}
        <div>
          <label className="block text-sm font-medium mb-2">Upload & Ingest Document</label>
          <div className="flex items-center gap-3">
            <input
              type="file"
              onChange={handleFileUpload}
              disabled={uploading}
              className="flex-1 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50"
              accept=".pdf,.doc,.docx,.txt,.csv,.json"
            />
            <Button
              onClick={() => document.querySelector('input[type="file"]').click()}
              disabled={uploading}
              className="flex items-center gap-2"
              variant="outline"
            >
              <Upload className="w-4 h-4" />
              {uploading ? 'Uploading...' : 'Choose File'}
            </Button>
          </div>
        </div>

        {/* Delete Section */}
        <div className="pt-4 border-t border-border/60">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-red-600">Danger Zone</h4>
              <p className="text-xs text-muted-foreground mt-1">
                Delete all knowledge base data for this company
              </p>
            </div>
            <Button
              onClick={handleDeleteData}
              disabled={deleting}
              variant="destructive"
              className="flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              {deleting ? 'Deleting...' : 'Delete Data'}
            </Button>
          </div>
        </div>

        {/* Message Display */}
        {message && (
          <div className={`flex items-center gap-2 p-3 rounded-lg ${
            messageType === 'success' 
              ? 'bg-green-50 text-green-700 border border-green-200' 
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
            {messageType === 'success' ? (
              <CheckCircle className="w-4 h-4 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
            )}
            <span className="text-sm">{message}</span>
          </div>
        )}

        {/* Instructions */}
        <div className="text-xs text-muted-foreground bg-gray-50 p-3 rounded-lg">
          <p className="font-medium mb-1">Supported formats:</p>
          <p>PDF, DOC, DOCX, TXT, CSV, JSON</p>
          <p className="mt-2">Documents will be processed and added to the knowledge base for AI assistance.</p>
        </div>
      </div>
    </Card>
  );
}
