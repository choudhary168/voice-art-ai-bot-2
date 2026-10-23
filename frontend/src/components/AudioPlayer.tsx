import React from 'react';
import { Volume2, VolumeX, Square } from 'lucide-react';

interface AudioPlayerProps {
  isPlaying: boolean;
  isMuted: boolean;
  onToggleMute: () => void;
  onInterrupt: () => void;
  outputSampleRate?: number;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  isPlaying,
  isMuted,
  onToggleMute,
  onInterrupt,
  outputSampleRate = 24000,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 18px',
        backgroundColor: 'rgba(15, 23, 42, 0.75)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '16px',
        fontSize: '0.85rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            backgroundColor: isMuted ? 'rgba(244, 63, 94, 0.15)' : 'rgba(99, 102, 241, 0.15)',
            color: isMuted ? '#fda4af' : '#a5b4fc',
          }}
        >
          {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
          {isPlaying && !isMuted && (
            <span
              style={{
                position: 'absolute',
                top: '-2px',
                right: '-2px',
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: '#818cf8',
                boxShadow: '0 0 8px #818cf8',
              }}
            />
          )}
        </div>
        <div>
          <div style={{ fontWeight: 600, color: '#f1f5f9' }}>
            {isPlaying ? 'Streaming Audio Playback' : 'Audio Engine Ready'}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
            PCM {outputSampleRate / 1000}kHz 16-bit mono • Gapless Stream
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {isPlaying && (
          <button
            onClick={onInterrupt}
            className="btn btn-rose"
            style={{ padding: '6px 12px', fontSize: '0.75rem' }}
            title="Interrupt agent speech and clear audio queue"
          >
            <Square size={12} fill="currentColor" />
            Interrupt
          </button>
        )}

        <button
          onClick={onToggleMute}
          className="btn btn-ghost"
          style={{
            padding: '8px',
            borderRadius: '10px',
            color: isMuted ? '#fda4af' : '#cbd5e1',
            borderColor: isMuted ? 'rgba(244, 63, 94, 0.4)' : 'rgba(255, 255, 255, 0.1)',
          }}
          title={isMuted ? 'Unmute' : 'Mute'}
        >
          {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
        </button>
      </div>
    </div>
  );
};
