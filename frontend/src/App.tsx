import React, { useState } from 'react';
import { Bot, BookOpen, AlertCircle, Sparkles, CheckCircle2 } from 'lucide-react';
import { useVoiceAgent } from './hooks/useVoiceAgent';
import { Visualizer } from './components/Visualizer';
import { AudioPlayer } from './components/AudioPlayer';
import { VoiceControls } from './components/VoiceControls';
import { ChatMessages } from './components/ChatMessages';
import { LatencyDiagnostics } from './components/LatencyDiagnostics';
import { VoiceSettings } from './components/VoiceSettings';

function getApiBaseUrl(): string {
  const envApiUrl = import.meta.env.VITE_API_URL;
  if (envApiUrl && typeof envApiUrl === 'string') {
    return envApiUrl.replace(/\/$/, '');
  }
  if (typeof window !== 'undefined' && window.location) {
    const loc = window.location;
    if (loc.hostname === 'localhost' || loc.hostname === '127.0.0.1') {
      return `${loc.protocol}//${loc.hostname}:8000`;
    }
    return loc.origin;
  }
  return 'http://localhost:8000';
}

export const App: React.FC = () => {
  const {
    connectionState,
    sessionInfo,
    messages,
    isVoiceMode,
    isPlayingAudio,
    isMuted,
    micLevel,
    agentAudioLevel,
    latencyMetrics,
    errorMessage,
    selectedVoice,
    setSelectedVoice,
    connect,
    disconnect,
    toggleVoiceMode,
    sendTextMessage,
    interrupt,
    toggleMute,
    clearChat,
  } = useVoiceAgent();

  const [showKnowledgeModal, setShowKnowledgeModal] = useState(false);
  const [docTitle, setDocTitle] = useState('');
  const [docContent, setDocContent] = useState('');
  const [docStatus, setDocStatus] = useState<string | null>(null);

  const handleAddKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docTitle.trim() || !docContent.trim()) return;

    try {
      const apiBase = getApiBaseUrl();
      const res = await fetch(`${apiBase}/api/knowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: docTitle.trim(),
          content: docContent.trim(),
          source: 'web-ui',
        }),
      });
      if (res.ok) {
        setDocStatus(`Document "${docTitle}" added successfully!`);
        setDocTitle('');
        setDocContent('');
        setTimeout(() => setDocStatus(null), 3000);
      }
    } catch (err) {
      setDocStatus('Failed to add document to backend.');
    }
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="app-header">
        <div className="brand-wrapper">
          <div className="brand-icon">
            <Bot size={26} />
          </div>
          <div>
            <h1 className="brand-title">Gemini 3.8 Live Voice Agent</h1>
            <div className="brand-subtitle">
              <span>Native Real-Time Multimodal Conversation</span>
              <span className="badge-live">● LIVE API</span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => setShowKnowledgeModal(true)}
            className="btn btn-ghost"
            style={{ padding: '8px 14px', fontSize: '0.8rem' }}
            title="Knowledge & Context Extension"
          >
            <BookOpen size={15} style={{ color: '#818cf8' }} />
            <span>Knowledge Store</span>
          </button>
        </div>
      </header>

      {/* Global Error Banner */}
      {errorMessage && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 18px',
            backgroundColor: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            borderRadius: '14px',
            color: '#fda4af',
            fontSize: '0.85rem',
            gap: '12px',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1 }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{errorMessage}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {connectionState !== 'connected' && (
              <button
                onClick={() => connect()}
                className="btn btn-rose"
                style={{ padding: '6px 12px', fontSize: '0.78rem' }}
              >
                Retry Connect
              </button>
            )}
          </div>
        </div>
      )}

      {/* Main Grid Layout */}
      <main className="main-grid">
        {/* Left: Chat Transcript and Controls */}
        <div className="chat-column">
          <VoiceSettings
            selectedVoice={selectedVoice}
            isConnected={connectionState === 'connected'}
            onVoiceChange={setSelectedVoice}
          />
          <ChatMessages
            messages={messages}
            onClear={clearChat}
            onSelectPrompt={(p) => {
              if (connectionState === 'connected') {
                sendTextMessage(p);
              }
            }}
            isConnected={connectionState === 'connected'}
          />

          <VoiceControls
            connectionState={connectionState}
            isVoiceMode={isVoiceMode}
            onConnect={() => connect()}
            onDisconnect={disconnect}
            onToggleVoiceMode={toggleVoiceMode}
            onSendText={sendTextMessage}
          />
        </div>

        {/* Right Sidebar: Visualizer, Audio Playback, and Diagnostics */}
        <aside className="sidebar-column">
          {/* Audio Visualizer */}
          <Visualizer
            micLevel={micLevel}
            agentAudioLevel={agentAudioLevel}
            isVoiceMode={isVoiceMode}
            isPlayingAudio={isPlayingAudio}
          />

          {/* Audio Playback Controls */}
          <AudioPlayer
            isPlaying={isPlayingAudio}
            isMuted={isMuted}
            onToggleMute={toggleMute}
            onInterrupt={interrupt}
            outputSampleRate={sessionInfo?.output_sample_rate || 24000}
          />

          {/* Telemetry and Latency Metrics */}
          <LatencyDiagnostics
            metrics={latencyMetrics}
            sessionInfo={sessionInfo}
          />

          {/* Architecture Highlights Card */}
          <div
            style={{
              padding: '16px',
              backgroundColor: 'rgba(15, 23, 42, 0.5)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '20px',
              fontSize: '0.78rem',
              color: '#94a3b8',
              lineHeight: 1.5,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                color: '#cbd5e1',
                fontWeight: 600,
                marginBottom: '8px',
              }}
            >
              <Sparkles size={14} style={{ color: '#6366f1' }} />
              <span>Unified Architecture</span>
            </div>
            <p style={{ margin: 0, marginBottom: '8px' }}>
              Gemini 3.8 Live processes audio natively end-to-end without separate external STT or TTS layers, eliminating cascading pipeline delays.
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
              <span style={{ padding: '2px 6px', borderRadius: '6px', backgroundColor: 'rgba(255,255,255,0.06)' }}>Mic: 16kHz PCM</span>
              <span style={{ padding: '2px 6px', borderRadius: '6px', backgroundColor: 'rgba(255,255,255,0.06)' }}>Spk: 24kHz PCM</span>
              <span style={{ padding: '2px 6px', borderRadius: '6px', backgroundColor: 'rgba(255,255,255,0.06)' }}>FastAPI WS</span>
            </div>
          </div>
        </aside>
      </main>

      {/* Knowledge Extension Modal */}
      {showKnowledgeModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '20px',
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: '520px',
              backgroundColor: '#0f172a',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '24px',
              padding: '24px',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <BookOpen size={20} style={{ color: '#818cf8' }} />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                  Dynamic Knowledge Extension
                </h3>
              </div>
              <button
                onClick={() => setShowKnowledgeModal(false)}
                className="btn btn-ghost"
                style={{ padding: '4px 10px', fontSize: '0.8rem' }}
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: '0.82rem', color: '#94a3b8', lineHeight: 1.5, marginBottom: '16px' }}>
              Inject website FAQs, documentation, or user-specific knowledge into the live agent.
              Gemini retrieves and references this context during conversation.
            </p>

            {docStatus && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  backgroundColor: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  color: '#6ee7b7',
                  fontSize: '0.8rem',
                  marginBottom: '16px',
                }}
              >
                <CheckCircle2 size={16} />
                <span>{docStatus}</span>
              </div>
            )}

            <form onSubmit={handleAddKnowledge} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                  Document / FAQ Title
                </label>
                <input
                  type="text"
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  placeholder="e.g. Return Policy, Pricing FAQ, User Guide"
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '12px',
                    backgroundColor: 'rgba(5, 8, 16, 0.7)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#f8fafc',
                    fontSize: '0.85rem',
                    outline: 'none',
                  }}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                  Knowledge Content
                </label>
                <textarea
                  value={docContent}
                  onChange={(e) => setDocContent(e.target.value)}
                  placeholder="Add specific knowledge or answers that the AI should know..."
                  rows={4}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '12px',
                    backgroundColor: 'rgba(5, 8, 16, 0.7)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#f8fafc',
                    fontSize: '0.85rem',
                    outline: 'none',
                    resize: 'vertical',
                  }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
                <button
                  type="button"
                  onClick={() => setShowKnowledgeModal(false)}
                  className="btn btn-ghost"
                >
                  Close
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                >
                  Add Document
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default App;
