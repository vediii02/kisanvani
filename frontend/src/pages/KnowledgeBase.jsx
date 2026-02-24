import React, { useEffect, useState } from 'react';
import { kbAPI } from '@/api/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Plus, Loader2, Edit, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

export default function KnowledgeBase() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    crop_name: '',
    problem_type: '',
    solution_steps: '',
    tags: '',
  });

  useEffect(() => {
    fetchEntries();
  }, []);

  const fetchEntries = async () => {
    try {
      const response = await kbAPI.getEntries();
      setEntries(response.data);
    } catch (error) {
      console.error('Error fetching KB entries:', error);
      toast.error('Failed to load KB entries');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await kbAPI.createEntry(formData);
      toast.success('KB entry created successfully');
      setDialogOpen(false);
      setFormData({ title: '', content: '', crop_name: '', problem_type: '', solution_steps: '', tags: '' });
      fetchEntries();
    } catch (error) {
      console.error('Error creating KB entry:', error);
      toast.error('Failed to create KB entry');
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
    <div className="space-y-6" data-testid="knowledge-base-page">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-4xl font-bold tracking-tight">Knowledge Base</h2>
          <p className="text-muted-foreground mt-2 text-lg">Manage agricultural advisory content</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-kb-entry-btn" className="rounded-full font-medium shadow-sm hover:shadow-md transition-all">
              <Plus className="w-4 h-4 mr-2" />
              Add Entry
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl" data-testid="kb-entry-dialog">
            <DialogHeader>
              <DialogTitle>Add Knowledge Base Entry</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="title">Title *</Label>
                <Input
                  id="title"
                  data-testid="kb-title-input"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label htmlFor="content">Content *</Label>
                <Textarea
                  id="content"
                  data-testid="kb-content-input"
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  rows={4}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="crop_name">Crop Name</Label>
                  <Input
                    id="crop_name"
                    data-testid="kb-crop-input"
                    value={formData.crop_name}
                    onChange={(e) => setFormData({ ...formData, crop_name: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="problem_type">Problem Type</Label>
                  <Input
                    id="problem_type"
                    data-testid="kb-problem-input"
                    value={formData.problem_type}
                    onChange={(e) => setFormData({ ...formData, problem_type: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="solution_steps">Solution Steps</Label>
                <Textarea
                  id="solution_steps"
                  data-testid="kb-solution-input"
                  value={formData.solution_steps}
                  onChange={(e) => setFormData({ ...formData, solution_steps: e.target.value })}
                  rows={3}
                />
              </div>
              <div>
                <Label htmlFor="tags">Tags (comma-separated)</Label>
                <Input
                  id="tags"
                  data-testid="kb-tags-input"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  placeholder="wheat,disease,fungal"
                />
              </div>
              <Button type="submit" data-testid="kb-submit-btn" className="w-full rounded-full">
                Create Entry
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {entries.map((entry) => (
          <Card key={entry.id} className="p-6 border border-border/60 hover:border-primary/20 transition-colors" data-testid={`kb-entry-card-${entry.id}`}>
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-semibold">{entry.title}</h3>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" data-testid={`edit-kb-${entry.id}`}>
                  <Edit className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm" data-testid={`delete-kb-${entry.id}`}>
                  <Trash2 className="w-4 h-4 text-destructive" />
                </Button>
              </div>
            </div>
            <p className="text-sm text-muted-foreground mb-4">{entry.content}</p>
            <div className="flex flex-wrap gap-2">
              {entry.crop_name && (
                <span className="text-xs px-3 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full">
                  {entry.crop_name}
                </span>
              )}
              {entry.problem_type && (
                <span className="text-xs px-3 py-1 bg-muted text-muted-foreground border border-border rounded-full">
                  {entry.problem_type}
                </span>
              )}
              {entry.is_approved && (
                <span className="text-xs px-3 py-1 bg-green-100 text-green-800 border border-green-200 rounded-full">
                  Approved
                </span>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}