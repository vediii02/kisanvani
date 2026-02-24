import React, { useEffect, useState } from 'react';
import { callsAPI } from '@/api/api';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2 } from 'lucide-react';
import { format } from 'date-fns';

export default function CallHistory() {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCalls();
  }, []);

  const fetchCalls = async () => {
    try {
      const response = await callsAPI.getCalls();
      setCalls(response.data);
    } catch (error) {
      console.error('Error fetching calls:', error);
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
    <div className="space-y-6" data-testid="call-history-page">
      <div>
        <h2 className="text-4xl font-bold tracking-tight">Call History</h2>
        <p className="text-muted-foreground mt-2 text-lg">View all voice call sessions</p>
      </div>

      <Card className="border border-border/60" data-testid="calls-list-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted border-b border-border">
              <tr>
                <th className="text-left p-4 font-semibold text-sm">Session ID</th>
                <th className="text-left p-4 font-semibold text-sm">Phone Number</th>
                <th className="text-left p-4 font-semibold text-sm">Provider</th>
                <th className="text-left p-4 font-semibold text-sm">Status</th>
                <th className="text-left p-4 font-semibold text-sm">Start Time</th>
                <th className="text-left p-4 font-semibold text-sm">Duration</th>
              </tr>
            </thead>
            <tbody>
              {calls.length === 0 ? (
                <tr>
                  <td colSpan="6" className="p-8 text-center text-muted-foreground">
                    No call sessions found
                  </td>
                </tr>
              ) : (
                calls.map((call) => (
                  <tr key={call.id} className="border-b border-border hover:bg-muted/50 transition-colors" data-testid={`call-row-${call.id}`}>
                    <td className="p-4 font-mono text-sm">{call.session_id}</td>
                    <td className="p-4 tabular-nums">{call.phone_number}</td>
                    <td className="p-4">{call.provider_name || 'N/A'}</td>
                    <td className="p-4">
                      <Badge
                        data-testid={`call-status-${call.id}`}
                        className={
                          call.status === 'active'
                            ? 'bg-green-100 text-green-800 border-green-200'
                            : call.status === 'completed'
                            ? 'bg-gray-100 text-gray-800 border-gray-200'
                            : 'bg-red-100 text-red-800 border-red-200'
                        }
                      >
                        {call.status}
                      </Badge>
                    </td>
                    <td className="p-4 text-sm">
                      {call.start_time ? format(new Date(call.start_time), 'MMM dd, yyyy HH:mm') : 'N/A'}
                    </td>
                    <td className="p-4 tabular-nums">{call.duration_seconds ? `${call.duration_seconds}s` : '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}