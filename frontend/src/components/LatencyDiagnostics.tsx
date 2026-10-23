import React, { useState } from 'react';
import { Activity, ChevronDown, ChevronUp, Gauge, Radio, Zap } from 'lucide-react';
import { LatencyMetrics, SessionReadyPayload } from '../types/events';

interface LatencyDiagnosticsProps {
  metrics: LatencyMetrics | null;
  sessionInfo: SessionReadyPayload | null;
}

export const LatencyDiagnostics: React.FC<LatencyDiagnosticsProps> = ({
  metrics,
  sessionInfo,
}) => {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div
      style={{
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        overflow: 'hidden',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
      }}
    >
      {/* Header bar */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 18px',
          backgroundColor: 'rgba(10, 15, 30, 0.6)',
          border: 'none',
          borderBottom: isOpen ? '1px solid rgba(255, 255, 255, 0.08)' : 'none',
          color: '#f8fafc',
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={16} style={{ color: '#34d399' }} />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            Latency & Telemetry
          </span>
          {metrics?.e2e_first_audio_ms && (
            <span
              style={{
                padding: '2px 8px',
                borderRadius: '9999px',
                fontSize: '0.72rem',
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                color: '#6ee7b7',
                border: '1px solid rgba(16, 185, 129, 0.3)',
              }}
            >
              {metrics.e2e_first_audio_ms} ms TTFB
            </span>
          )}
        </div>
        {isOpen ? <ChevronUp size={16} color="#94a3b8" /> : <ChevronDown size={16} color="#94a3b8" />}
      </button>

      {/* Body */}
      {isOpen && (
        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Key Latency Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: '10px',
            }}
          >
            <div
              style={{
                padding: '12px',
                borderRadius: '14px',
                backgroundColor: 'rgba(5, 8, 16, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.75rem' }}>
                <span>1st Audio Chunk</span>
                <Zap size={13} style={{ color: '#fbbf24' }} />
              </div>
              <div style={{ marginTop: '8px', fontSize: '1.25rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#f8fafc' }}>
                {metrics?.e2e_first_audio_ms != null ? (
                  <span style={{ color: '#fbbf24' }}>{metrics.e2e_first_audio_ms} ms</span>
                ) : (
                  <span style={{ color: '#64748b', fontSize: '0.85rem', fontWeight: 400 }}>Waiting...</span>
                )}
              </div>
              <div style={{ fontSize: '0.65rem', color: '#64748b', marginTop: '4px' }}>Input → Audio out</div>
            </div>

            <div
              style={{
                padding: '12px',
                borderRadius: '14px',
                backgroundColor: 'rgba(5, 8, 16, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.75rem' }}>
                <span>1st Transcript</span>
                <Radio size={13} style={{ color: '#818cf8' }} />
              </div>
              <div style={{ marginTop: '8px', fontSize: '1.25rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#f8fafc' }}>
                {metrics?.e2e_first_transcription_ms != null ? (
                  <span style={{ color: '#818cf8' }}>{metrics.e2e_first_transcription_ms} ms</span>
                ) : (
                  <span style={{ color: '#64748b', fontSize: '0.85rem', fontWeight: 400 }}>—</span>
                )}
              </div>
              <div style={{ fontSize: '0.65rem', color: '#64748b', marginTop: '4px' }}>Input → 1st Text</div>
            </div>

            <div
              style={{
                padding: '12px',
                borderRadius: '14px',
                backgroundColor: 'rgba(5, 8, 16, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.75rem' }}>
                <span>Turn Duration</span>
                <Gauge size={13} style={{ color: '#34d399' }} />
              </div>
              <div style={{ marginTop: '8px', fontSize: '1.25rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#f8fafc' }}>
                {metrics?.total_turn_duration_ms != null ? (
                  <span style={{ color: '#34d399' }}>{metrics.total_turn_duration_ms} ms</span>
                ) : (
                  <span style={{ color: '#64748b', fontSize: '0.85rem', fontWeight: 400 }}>—</span>
                )}
              </div>
              <div style={{ fontSize: '0.65rem', color: '#64748b', marginTop: '4px' }}>Full turn synthesis</div>
            </div>
          </div>

          {/* Model & Audio Pipeline Specs */}
          <div
            style={{
              padding: '12px',
              borderRadius: '14px',
              backgroundColor: 'rgba(5, 8, 16, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '10px',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <div>
              <div style={{ color: '#64748b', fontSize: '0.65rem', textTransform: 'uppercase' }}>Model</div>
              <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{sessionInfo?.model || 'gemini-3.8-live'}</div>
            </div>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.65rem', textTransform: 'uppercase' }}>Voice</div>
              <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{sessionInfo?.voice || 'Puck'}</div>
            </div>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.65rem', textTransform: 'uppercase' }}>Input Rate</div>
              <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{sessionInfo?.input_sample_rate || 16000} Hz PCM</div>
            </div>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.65rem', textTransform: 'uppercase' }}>Output Rate</div>
              <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{sessionInfo?.output_sample_rate || 24000} Hz PCM</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
