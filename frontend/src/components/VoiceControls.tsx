import React, { useState } from 'react';
import { Mic, MicOff, Send, Power, PowerOff, Sparkles } from 'lucide-react';
import { ConnectionState } from '../types/events';

interface VoiceControlsProps {
  connectionState: ConnectionState;
  isVoiceMode: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
  onToggleVoiceMode: () => void;
  onSendText: (text: string) => void;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  connectionState,
  isVoiceMode,
  onConnect,
  onDisconnect,
  onToggleVoiceMode,
  onSendText,
}) => {
  const [inputText, setInputText] = useState('');

  const isConnected = connectionState === 'connected';
  const isConnecting = connectionState === 'connecting';

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || !isConnected) return;
    onSendText(inputText);
    setInputText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%' }}>
      {/* Voice and Session Action Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 16px',
          backgroundColor: 'rgba(15, 23, 42, 0.75)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '18px',
          gap: '12px',
          flexWrap: 'wrap',
        }}
      >
        {/* Connect / Disconnect Action */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isConnected ? (
            <button
              onClick={onDisconnect}
              className="btn btn-rose"
              style={{ padding: '8px 14px', fontSize: '0.8rem' }}
            >
              <PowerOff size={14} />
              Disconnect
            </button>
          ) : (
            <button
              onClick={onConnect}
              disabled={isConnecting}
              className="btn btn-primary"
              style={{ padding: '8px 16px', fontSize: '0.8rem' }}
            >
              <Power size={14} />
              {isConnecting ? 'Connecting...' : 'Connect Session'}
            </button>
          )}

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 10px',
              borderRadius: '9999px',
              backgroundColor: 'rgba(5, 8, 16, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              fontSize: '0.72rem',
              fontFamily: 'var(--font-mono)',
              color: '#cbd5e1',
            }}
          >
            <span
              style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: isConnected ? '#34d399' : isConnecting ? '#fbbf24' : '#64748b',
                boxShadow: isConnected ? '0 0 8px #34d399' : 'none',
              }}
            />
            <span style={{ textTransform: 'capitalize' }}>{connectionState}</span>
          </div>
        </div>

        {/* Center Mic Big Button */}
        <button
          onClick={onToggleVoiceMode}
          disabled={isConnecting}
          className={`btn ${isVoiceMode ? 'pulse-recording' : 'btn-emerald'}`}
          style={{
            padding: '10px 20px',
            fontSize: '0.88rem',
            letterSpacing: '0.02em',
          }}
          title={isVoiceMode ? 'Stop Microphone' : 'Enable Real-Time Voice'}
        >
          {isVoiceMode ? <MicOff size={18} /> : <Mic size={18} />}
          <span>{isVoiceMode ? 'Stop Voice Mode' : 'Start Voice Mode'}</span>
        </button>

        {/* Language Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.72rem',
            color: '#a5b4fc',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            padding: '6px 12px',
            borderRadius: '10px',
            border: '1px solid rgba(99, 102, 241, 0.25)',
          }}
        >
          <Sparkles size={13} style={{ color: '#818cf8' }} />
          <span>English • हिन्दी • Hinglish</span>
        </div>
      </div>

      {/* Typed Input Field */}
      <form
        onSubmit={handleSend}
        style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          width: '100%',
        }}
      >
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!isConnected}
          placeholder={
            isConnected
              ? 'Type a question in English, Hindi, or Hinglish (e.g., "Tell me about quantum computing")...'
              : 'Connect session to ask questions via speech or text...'
          }
          style={{
            width: '100%',
            padding: '14px 50px 14px 18px',
            backgroundColor: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: '16px',
            fontSize: '0.9rem',
            color: '#f8fafc',
            outline: 'none',
            fontFamily: 'var(--font-sans)',
            boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.4)',
            transition: 'border-color 0.2s',
          }}
          onFocus={(e) => (e.target.style.borderColor = 'rgba(99, 102, 241, 0.6)')}
          onBlur={(e) => (e.target.style.borderColor = 'rgba(255, 255, 255, 0.12)')}
        />
        <button
          type="submit"
          disabled={!isConnected || !inputText.trim()}
          className="btn btn-primary"
          style={{
            position: 'absolute',
            right: '8px',
            padding: '8px 12px',
            borderRadius: '10px',
          }}
          title="Send message"
        >
          <Send size={15} />
        </button>
      </form>
    </div>
  );
};
