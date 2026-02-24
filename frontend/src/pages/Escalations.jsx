import React, { useEffect, useState } from 'react';
import { adminAPI } from '@/api/api';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2 } from 'lucide-react';
import { format } from 'date-fns';

export default function Escalations() {
  const [escalations, setEscalations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEscalations();
  }, []);

  const fetchEscalations = async () => {
    try {
      const response = await adminAPI.getEscalations();
      setEscalations(response.data);
    } catch (error) {
      console.error('Error fetching escalations:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen" data-testid="loading-spinner">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="escalations-page">
      <div>
        <h2 className="text-4xl font-bold tracking-tight">Escalations</h2>
        <p className="text-muted-foreground mt-2 text-lg">Cases requiring expert review</p>
      </div>

      <div className="space-y-4">
        {escalations.length === 0 ? (
          <Card className="p-12 text-center border border-border/60" data-testid="no-escalations">
            <p className="text-muted-foreground">No escalations found</p>
          </Card>
        ) : (
          escalations.map((escalation) => (
            <Card key={escalation.id} className="p-6 border border-border/60 hover:border-secondary/40 transition-colors" data-testid={`escalation-card-${escalation.id}`}>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <h3 className="text-lg font-semibold">Case #{escalation.case_id}</h3>
                    <Badge
                      className={
                        escalation.status === 'pending'
                          ? 'bg-yellow-100 text-yellow-800 border-yellow-200'
                          : escalation.status === 'in_review'
                          ? 'bg-blue-100 text-blue-800 border-blue-200'
                          : 'bg-gray-100 text-gray-800 border-gray-200'
                      }
                      data-testid={`escalation-status-${escalation.id}`}
                    >
                      {escalation.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    <strong>Reason:</strong> {escalation.reason}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    <strong>Confidence Score:</strong> {escalation.confidence_score}
                  </p>
                  <p className="text-xs text-muted-foreground mt-3">
                    Created: {format(new Date(escalation.created_at), 'MMM dd, yyyy HH:mm')}
                  </p>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}