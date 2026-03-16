import React, { useState, useEffect, useRef } from 'react';
import { Phone, PhoneOff, Mic, MicOff, Volume2, Activity } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

// Audio Context variables
let audioContext = null;
let mediaStream = null;
let scriptProcessor = null;
let mediaSource = null;

const CallSimulator = () => {
    const [status, setStatus] = useState('disconnected'); // disconnected, connecting, connected
    const [logs, setLogs] = useState([]);
    const [wsUrl, setWsUrl] = useState('');
    const [orgId, setOrgId] = useState('1');
    const [fromNumber, setFromNumber] = useState('+919999999999');
    const [isMuted, setIsMuted] = useState(false);

    const wsRef = useRef(null);
    const audioContextRef = useRef(null);
    const nextPlayTimeRef = useRef(0);
    const totalTtsBytesRef = useRef(0);
    const totalTtsChunksRef = useRef(0);
    const currentSourcesRef = useRef([]); // Track active TTS AudioBufferSourceNodes for hard stop on barge-in

    // Initialize WS URL on mount
    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Remove the port logic for dev or hardcode 8001 since the backend is at 8001
        const host = window.location.hostname;
        // Set default target WS. Using localhost:8001 for local backend
        setWsUrl(`${protocol}//localhost:8001/ws/conversation`);
    }, []);

    const addLog = (msg, type = 'info') => {
        setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), msg, type }]);
    };

    const downsampleBuffer = (buffer, sampleRate, outSampleRate) => {
        if (outSampleRate === sampleRate) return buffer;
        if (outSampleRate > sampleRate) throw new Error("Downsampling rate should be smaller");

        var sampleRateRatio = sampleRate / outSampleRate;
        var newLength = Math.round(buffer.length / sampleRateRatio);
        var result = new Int16Array(newLength);
        var offsetResult = 0;
        var offsetBuffer = 0;

        while (offsetResult < result.length) {
            var nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
            var accum = 0, count = 0;
            for (var i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
                accum += buffer[i];
                count++;
            }
            result[offsetResult] = Math.min(1, Math.max(-1, accum / count)) * 0x7FFF;
            offsetResult++;
            offsetBuffer = nextOffsetBuffer;
        }
        return result.buffer;
    };

    const floatTo16BitPCM = (input) => {
        const output = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
            const s = Math.max(-1, Math.min(1, input[i]));
            output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return output.buffer;
    };

    const playAudioChunk = (base64Audio) => {
        if (!audioContextRef.current) return;

        // Convert base64 or raw bytes. The backend sends pure binary bytes via websocket.send_bytes
        // We get a Blob or ArrayBuffer from WebSocket
    };

    const startCall = async () => {
        if (status !== 'disconnected') return;

        setStatus('connecting');
        setLogs([]);
        addLog('Requesting microphone access...', 'info');

        try {
            mediaStream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
            addLog('Microphone access granted.', 'success');

            // Setting up Web Audio API
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            audioContextRef.current = audioContext;

            // CRITICAL: Resume AudioContext immediately after user gesture (click)
            // Browsers suspend AudioContext by default and require resume() after interaction
            if (audioContext.state === 'suspended') {
                await audioContext.resume();
                addLog('AudioContext resumed after user gesture.', 'info');
            }

            // Create a gain node for volume control (ensures audio is audible)
            const gainNode = audioContext.createGain();
            gainNode.gain.value = 1.0;
            gainNode.connect(audioContext.destination);

            // Store gain node for use in playback
            audioContextRef.current._gainNode = gainNode;

            mediaSource = audioContext.createMediaStreamSource(mediaStream);
            scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);

            mediaSource.connect(scriptProcessor);
            scriptProcessor.connect(audioContext.destination);

            scriptProcessor.onaudioprocess = (e) => {
                if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || isMuted) return;

                const inputData = e.inputBuffer.getChannelData(0);
                const sampleRate = audioContext.sampleRate;
                const outSampleRate = 8000;

                const pcmBuffer = downsampleBuffer(inputData, sampleRate, outSampleRate);
                wsRef.current.send(pcmBuffer);
            };

            // Connect WebSocket
            const url = `${wsUrl}?org_id=${orgId}&from_number=${encodeURIComponent(fromNumber)}`;
            addLog(`Connecting to ${url}...`, 'info');

            const ws = new WebSocket(url);
            ws.binaryType = 'arraybuffer'; // Expect binary incoming audio
            wsRef.current = ws;

            ws.onopen = () => {
                setStatus('connected');
                addLog('WebSocket connected. Call started.', 'success');
            };

            ws.onmessage = async (event) => {
                if (typeof event.data === 'string') {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'stt_output') {
                            addLog(`User: ${data.transcript}`, 'user');
                        } else if (data.type === 'stt_chunk') {
                            // Ignore chunks in log to reduce spam
                        } else if (data.type === 'agent_chunk') {
                            addLog(`Agent: ${data.text}`, 'agent');
                        } else if (data.type === 'barge_in') {
                            addLog(`Agent interrupted by barge-in`, 'warning');
                            // Stop all currently playing TTS sources immediately to prevent overlapping audio
                            try {
                                currentSourcesRef.current.forEach(src => {
                                    try {
                                        src.stop();
                                    } catch (e) {
                                        // ignore individual stop errors
                                    }
                                });
                            } finally {
                                currentSourcesRef.current = [];
                            }
                            // Reset playback schedule on barge-in so next audio plays immediately
                            nextPlayTimeRef.current = 0;
                        } else if (data.type === 'hangup') {
                            addLog(`Call ended by server: ${data.reason}`, 'error');
                            stopCall();
                        } else {
                            addLog(`Received: ${event.data}`, 'info');
                        }
                    } catch (e) {
                        addLog(`Error parsing JSON: ${e.message}`, 'error');
                    }
                } else {
                    // Binary audio chunk (TTS) received
                    const ctx = audioContextRef.current;
                    if (!ctx) return;
                    const audioData = event.data; // ArrayBuffer
                    if (!audioData || audioData.byteLength === 0) {
                        addLog('Received empty audio chunk (0 bytes)', 'warning');
                        return;
                    }

                    // Ensure buffer length is even so Int16Array views are valid
                    if (audioData.byteLength % 2 !== 0) {
                        addLog(`Dropping malformed audio chunk (odd length=${audioData.byteLength})`, 'error');
                        return;
                    }

                    // Ensure AudioContext is still running (can get suspended by browser tab switch)
                    if (ctx.state === 'suspended') {
                        try { await ctx.resume(); } catch (e) { /* ignore */ }
                    }

                    try {
                        const pcm16 = new Int16Array(audioData);
                        const float32 = new Float32Array(pcm16.length);
                        for (let i = 0; i < pcm16.length; i++) {
                            float32[i] = pcm16[i] / (pcm16[i] < 0 ? 32768 : 32767);
                        }

                        const audioBuffer = ctx.createBuffer(1, float32.length, 8000);
                        audioBuffer.getChannelData(0).set(float32);

                        const source = ctx.createBufferSource();
                        source.buffer = audioBuffer;
                        // Connect through gain node for reliable volume
                        const gainNode = ctx._gainNode || ctx.destination;
                        source.connect(gainNode);

                        // Sequential playback: schedule chunks back-to-back
                        const duration = audioBuffer.duration;
                        totalTtsBytesRef.current += audioData.byteLength;
                        totalTtsChunksRef.current += 1;
                        addLog(
                            `TTS audio received: ${audioData.byteLength} bytes (~${duration.toFixed(3)}s). ` +
                            `Session total=${totalTtsChunksRef.current} chunks / ${totalTtsBytesRef.current} bytes.`,
                            'info'
                        );
                        if (nextPlayTimeRef.current < ctx.currentTime) {
                            nextPlayTimeRef.current = ctx.currentTime;
                        }
                        // Track this source so we can hard-stop it on barge-in
                        currentSourcesRef.current.push(source);
                        source.onended = () => {
                            currentSourcesRef.current = currentSourcesRef.current.filter(s => s !== source);
                        };
                        source.start(nextPlayTimeRef.current);
                        nextPlayTimeRef.current += audioBuffer.duration;

                    } catch (e) {
                        console.error("Error decoding audio", e);
                    }
                }
            };

            ws.onclose = () => {
                addLog('WebSocket closed.', 'warning');
                stopCall();
            };

            ws.onerror = (err) => {
                addLog(`WebSocket error: ${err.message || 'Unknown'}`, 'error');
            };

        } catch (e) {
            addLog(`Failed to access microphone: ${e.message}`, 'error');
            toast.error('Microphone access is required');
            stopCall();
        }
    };

    const stopCall = () => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        if (scriptProcessor) {
            scriptProcessor.disconnect();
            scriptProcessor = null;
        }
        if (mediaSource) {
            mediaSource.disconnect();
            mediaSource = null;
        }
        if (mediaStream) {
            mediaStream.getTracks().forEach(t => t.stop());
            mediaStream = null;
        }
        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }
        setStatus('disconnected');
        addLog('Call disconnected.', 'info');
    };

    const toggleMute = () => {
        setIsMuted(!isMuted);
        addLog(`Microphone ${!isMuted ? 'muted' : 'unmuted'}`, 'info');
    };

    // Auto scroll logs
    const logsEndRef = useRef(null);
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    // Clean up on unmount
    useEffect(() => {
        return () => {
            stopCall();
        };
    }, []);

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Simulator (Alpha)</h1>
                    <p className="text-muted-foreground mt-2">Test your AI agents without dialing real numbers. Works natively in the browser via WebSockets.</p>
                </div>
                <Badge variant={status === 'connected' ? 'success' : status === 'connecting' ? 'warning' : 'secondary'} className="px-4 py-1 text-sm rounded-full">
                    {status === 'connected' ? <><Activity className="w-4 h-4 mr-2 animate-pulse" /> Live Call</> : status === 'connecting' ? 'Connecting...' : 'Ready'}
                </Badge>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Controls Panel */}
                <Card className="col-span-1 border-0 shadow-lg bg-card/50 backdrop-blur-sm rounded-2xl overflow-hidden">
                    <div className="h-2 w-full bg-gradient-to-r from-blue-500 to-emerald-500" />
                    <CardHeader>
                        <CardTitle>Session Parameters</CardTitle>
                        <CardDescription>Configure the connection specifics</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="space-y-2">
                            <Label htmlFor="wsUrl">WebSocket Endpoint</Label>
                            <Input
                                id="wsUrl"
                                value={wsUrl}
                                onChange={e => setWsUrl(e.target.value)}
                                disabled={status !== 'disconnected'}
                                className="font-mono text-xs"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="orgId">Organisation ID</Label>
                                <Input
                                    id="orgId"
                                    value={orgId}
                                    onChange={e => setOrgId(e.target.value)}
                                    disabled={status !== 'disconnected'}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="fromNumber">Simulated Caller</Label>
                                <Input
                                    id="fromNumber"
                                    value={fromNumber}
                                    onChange={e => setFromNumber(e.target.value)}
                                    disabled={status !== 'disconnected'}
                                />
                            </div>
                        </div>

                        <div className="pt-4 border-t flex flex-col gap-3">
                            {status === 'disconnected' ? (
                                <Button
                                    onClick={startCall}
                                    size="lg"
                                    className="w-full h-14 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white rounded-xl shadow-lg shadow-emerald-500/20 transition-all hover:scale-[1.02]"
                                >
                                    <Phone className="w-5 h-5 mr-chat mr-2" fill="currentColor" /> Start Voice Connection
                                </Button>
                            ) : (
                                <div className="flex gap-3">
                                    <Button
                                        variant="destructive"
                                        onClick={stopCall}
                                        size="lg"
                                        className="flex-1 h-14 rounded-xl shadow-lg shadow-red-500/20"
                                    >
                                        <PhoneOff className="w-5 h-5 mr-2" /> End Call
                                    </Button>

                                    <Button
                                        variant="outline"
                                        onClick={toggleMute}
                                        size="lg"
                                        className={`h-14 w-14 p-0 rounded-xl border-2 ${isMuted ? 'border-red-500 text-red-500 bg-red-50' : 'border-slate-200'}`}
                                    >
                                        {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                                    </Button>
                                </div>
                            )}
                        </div>

                        {status === 'connected' && (
                            <div className="p-4 bg-emerald-50 text-emerald-700 rounded-xl text-sm font-medium flex items-center shadow-inner border border-emerald-100">
                                <Volume2 className="w-4 h-4 mr-2 animate-pulse" /> Audio streaming to server at 8kHz PCM.
                            </div>
                        )}

                    </CardContent>
                </Card>

                {/* Console / Transcript Panel */}
                <Card className="col-span-1 lg:col-span-2 border-0 shadow-lg bg-card rounded-2xl overflow-hidden flex flex-col h-[600px]">
                    <div className="bg-slate-900 border-b border-slate-800 p-3 px-5 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-500" />
                            <div className="w-3 h-3 rounded-full bg-amber-500" />
                            <div className="w-3 h-3 rounded-full bg-green-500" />
                            <span className="text-slate-400 text-sm font-mono ml-2 font-medium">realtime_stream_log</span>
                        </div>
                    </div>
                    <CardContent className="p-0 flex-1 overflow-hidden flex flex-col bg-slate-950">
                        <div className="flex-1 overflow-y-auto p-6 space-y-4">
                            {logs.length === 0 && (
                                <div className="h-full flex items-center justify-center text-slate-600 font-mono text-sm opacity-50">
                                    Waiting for connection...
                                </div>
                            )}
                            {logs.map((log, i) => (
                                <div key={i} className={`font-mono text-sm flex items-start gap-4 p-2 rounded-lg transition-colors ${log.type === 'user' ? 'bg-blue-900/20 text-blue-200 border border-blue-800/30' :
                                    log.type === 'agent' ? 'bg-emerald-900/20 text-emerald-200 border border-emerald-800/30' :
                                        log.type === 'error' ? 'text-red-400' :
                                            log.type === 'warning' ? 'text-amber-400' :
                                                log.type === 'success' ? 'text-green-400' :
                                                    'text-slate-400'
                                    }`}>
                                    <span className="opacity-40 text-xs mt-0.5 min-w-[70px]">{log.time}</span>
                                    <div className="flex-1 break-words">
                                        {log.type === 'user' && <span className="font-bold mr-2 text-blue-400">Caller:</span>}
                                        {log.type === 'agent' && <span className="font-bold mr-2 text-emerald-400">Agent:</span>}
                                        {log.msg}
                                    </div>
                                </div>
                            ))}
                            <div ref={logsEndRef} />
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default CallSimulator;
