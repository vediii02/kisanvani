import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, Brain, Settings, Database, Zap, AlertTriangle, CheckCircle, Save } from 'lucide-react';
import { toast } from 'sonner';
import api from '../api/api';

export default function SuperAdminAIManagement() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [health, setHealth] = useState({
    status: 'healthy',
    system: 'operational',
    services: { database: 'connected', redis: 'connected' },
    active_alerts: 0
  });
  const [formData, setFormData] = useState({
    ai_confidence_threshold: 70,
    max_call_duration_minutes: 15,
    default_language: 'hi',
    stt_provider: 'sarvam',
    tts_provider: 'sarvam',
    llm_model: 'groq',
    rag_strictness_level: 'medium',
    rag_min_confidence: 60,
    force_kb_approval: true,
    enable_call_recording: true,
    enable_auto_escalation: true,
    max_concurrent_calls: 100
  });

  useEffect(() => {
    fetchConfig();
    fetchHealth();
    // Poll health every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const response = await api.get('/health');
      setHealth(response.data);
    } catch (error) {
      console.error('Error fetching health status:', error);
    }
  };

  const fetchConfig = async () => {
    try {
      const response = await api.get('/superadmin/platform/config');
      const data = response.data;

      // Normalize data: ensure providers are valid options we support
      // If DB has old values like 'bhashini' or 'google', map them to 'sarvam' or 'groq'
      const normalizedData = {
        ...data,
        stt_provider: ['sarvam', 'google'].includes(data.stt_provider) ? data.stt_provider : 'google',
        tts_provider: ['sarvam', 'google', 'cartesia'].includes(data.tts_provider) ? data.tts_provider : 'google',
        llm_model: ['groq', 'openai', 'gemini'].includes(data.llm_model) ? data.llm_model : 'groq',
      };

      setConfig(normalizedData);
      setFormData(normalizedData);
    } catch (error) {
      console.error('Error fetching config:', error);
      toast.error('Failed to load AI configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/superadmin/platform/config', formData);
      toast.success('AI configuration updated successfully');
      fetchConfig();
    } catch (error) {
      console.error('Error saving config:', error);
      toast.error('Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 max-w-5xl">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Brain className="h-8 w-8 text-primary" />
            AI Management
          </h1>
          <p className="text-muted-foreground mt-2">Configure AI models, RAG settings, and system behavior</p>
        </div>
        <Button onClick={handleSave} disabled={saving} className="flex items-center gap-2">
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          Save Changes
        </Button>
      </div>

      {/* AI Models Section */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Settings className="h-5 w-5 text-blue-600" />
          AI Models & Providers
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Speech-to-Text Provider</label>
            <select
              value={formData.stt_provider}
              onChange={(e) => setFormData({ ...formData, stt_provider: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="sarvam">Sarvam AI</option>
              <option value="google">Google</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Text-to-Speech Provider</label>
            <select
              value={formData.tts_provider}
              onChange={(e) => setFormData({ ...formData, tts_provider: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="sarvam">Sarvam AI</option>
              <option value="google">Google</option>
              <option value="cartesia">Cartesia AI</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">LLM Model</label>
            <select
              value={formData.llm_model}
              onChange={(e) => setFormData({ ...formData, llm_model: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="groq">Groq (Llama 3.1)</option>
              <option value="openai">OpenAI (GPT-4o)</option>
              <option value="gemini">Google (Gemini)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Embedding Model (auto)</label>
            <div className="w-full px-3 py-2 border rounded-md bg-gray-50 text-gray-700 text-sm">
              {formData.llm_model === 'gemini'
                ? '🟢 Google (gemini-embedding-001)'
                : '🔵 OpenAI (text-embedding-3-small)'}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Auto-selected based on LLM model. Used for KB & product vectorization.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Default Language</label>
            <select
              value={formData.default_language}
              onChange={(e) => setFormData({ ...formData, default_language: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="hi">Hindi (हिंदी)</option>
              <option value="en">English</option>
              <option value="pa">Punjabi (ਪੰਜਾਬੀ)</option>
              <option value="mr">Marathi (मराठी)</option>
            </select>
          </div>
        </div>
      </Card>

      {/* RAG Configuration */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Database className="h-5 w-5 text-green-600" />
          RAG & Knowledge Base Settings
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">RAG Strictness Level</label>
            <select
              value={formData.rag_strictness_level}
              onChange={(e) => setFormData({ ...formData, rag_strictness_level: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="low">Low - More flexible responses</option>
              <option value="medium">Medium - Balanced approach</option>
              <option value="high">High - Strict KB adherence</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Minimum RAG Confidence: {formData.rag_min_confidence}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={formData.rag_min_confidence}
              onChange={(e) => setFormData({ ...formData, rag_min_confidence: parseInt(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Less Strict</span>
              <span>More Strict</span>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
            <input
              type="checkbox"
              id="force_kb_approval"
              checked={formData.force_kb_approval}
              onChange={(e) => setFormData({ ...formData, force_kb_approval: e.target.checked })}
              className="rounded"
            />
            <label htmlFor="force_kb_approval" className="text-sm font-medium">
              Force KB Approval (AI can't answer without KB match)
            </label>
          </div>
        </div>
      </Card>

      {/* Call Management */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Zap className="h-5 w-5 text-orange-600" />
          Call Management
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              AI Confidence Threshold: {formData.ai_confidence_threshold}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={formData.ai_confidence_threshold}
              onChange={(e) => setFormData({ ...formData, ai_confidence_threshold: parseInt(e.target.value) })}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Below this threshold, calls will be escalated to human agents
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Max Call Duration (minutes)</label>
            <Input
              type="number"
              min="5"
              max="60"
              value={formData.max_call_duration_minutes}
              onChange={(e) => setFormData({ ...formData, max_call_duration_minutes: parseInt(e.target.value) })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Max Concurrent Calls</label>
            <Input
              type="number"
              min="10"
              max="1000"
              value={formData.max_concurrent_calls}
              onChange={(e) => setFormData({ ...formData, max_concurrent_calls: parseInt(e.target.value) })}
            />
          </div>

          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <input
                type="checkbox"
                id="enable_call_recording"
                checked={formData.enable_call_recording}
                onChange={(e) => setFormData({ ...formData, enable_call_recording: e.target.checked })}
                className="rounded"
              />
              <label htmlFor="enable_call_recording" className="text-sm font-medium">
                Enable Call Recording
              </label>
            </div>

            <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg border border-green-200">
              <input
                type="checkbox"
                id="enable_auto_escalation"
                checked={formData.enable_auto_escalation}
                onChange={(e) => setFormData({ ...formData, enable_auto_escalation: e.target.checked })}
                className="rounded"
              />
              <label htmlFor="enable_auto_escalation" className="text-sm font-medium">
                Enable Auto-Escalation
              </label>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className={`h-8 w-8 ${health.system === 'operational' ? 'text-green-600' : 'text-amber-600'}`} />
            <div>
              <p className="text-sm text-gray-600">AI System Status</p>
              <p className="text-lg font-bold capitalize">{health.system}</p>
            </div>
          </div>
        </Card>


        <Card className="p-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className={`h-8 w-8 ${health.active_alerts > 0 ? 'text-red-600' : 'text-yellow-600'}`} />
            <div>
              <p className="text-sm text-gray-600">Active Alerts</p>
              <p className="text-lg font-bold">{health.active_alerts}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Warning Box */}
      <Card className="p-4 bg-red-50 border-red-200">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-6 w-6 text-red-600 mt-0.5" />
          <div>
            <h4 className="font-bold text-red-800 mb-1">Configuration Warning</h4>
            <p className="text-sm text-red-700">
              Changes to AI configuration will affect all ongoing and future calls across the platform.
              Test thoroughly before applying in production. High confidence thresholds may increase
              escalation rates.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
