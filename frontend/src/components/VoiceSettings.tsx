import React from 'react';
import { ExternalLink, Volume2 } from 'lucide-react';
import { LIVE_VOICES, LiveVoiceName } from '../config/voices';

interface VoiceSettingsProps {
  selectedVoice: LiveVoiceName;
  isConnected: boolean;
  onVoiceChange: (voice: LiveVoiceName) => void;
}

export const VoiceSettings: React.FC<VoiceSettingsProps> = ({
  selectedVoice,
  isConnected,
  onVoiceChange,
}) => {
  const selected = LIVE_VOICES.find((voice) => voice.name === selectedVoice) ?? LIVE_VOICES[1];

  return (
    <section
      aria-label="Voice settings"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
        flexWrap: 'wrap',
        padding: '14px 16px',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '16px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '9px', flex: '1 1 160px' }}>
        <Volume2 size={17} style={{ color: '#a5b4fc' }} />
        <div>
          <div style={{ color: 'var(--text-main)', fontWeight: 600, fontSize: '0.84rem' }}>Agent voice</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Google Gemini Live</div>
        </div>
      </div>

      <label style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: '1 1 240px' }}>
        <select
          aria-label="Choose agent voice"
          value={selectedVoice}
          onChange={(event) => onVoiceChange(event.target.value as LiveVoiceName)}
          style={{
            flex: 1,
            minWidth: 150,
            padding: '10px 12px',
            color: 'var(--text-main)',
            background: 'rgba(5, 8, 16, 0.75)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 10,
            font: 'inherit',
          }}
        >
          {LIVE_VOICES.map((voice) => (
            <option key={voice.name} value={voice.name}>
              {voice.name} - {voice.style}
            </option>
          ))}
        </select>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', minWidth: 82 }}>{selected.style}</span>
      </label>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexBasis: '100%', justifyContent: 'space-between' }}>
        <span style={{ color: 'var(--text-faint)', fontSize: '0.72rem' }}>
          {isConnected ? 'Saved for your next session; the active voice stays the same.' : 'Saved on this device and used for your next session.'}
        </span>
        <a
          href="https://aistudio.google.com/"
          target="_blank"
          rel="noreferrer"
          style={{ display: 'inline-flex', alignItems: 'center', gap: 5, color: '#a5b4fc', fontSize: '0.72rem', textDecoration: 'none', whiteSpace: 'nowrap' }}
        >
          <ExternalLink size={12} /> Hear samples in AI Studio
        </a>
      </div>
    </section>
  );
};
