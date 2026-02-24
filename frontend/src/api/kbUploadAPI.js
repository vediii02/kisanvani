// Add KB upload API for PDF/CSV (admin, org)
import api from './api';

export const kbUploadAPI = {
  // Admin: orgId required, Org-admin: orgId auto (backend)
  upload: (file, orgId = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (orgId) formData.append('organisation_id', orgId);
    return api.post('/kb/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};
