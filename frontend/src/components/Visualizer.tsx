import React, { useEffect, useRef } from 'react';

interface VisualizerProps {
  micLevel: number;
  agentAudioLevel: number;
  isVoiceMode: boolean;
  isPlayingAudio: boolean;
}

export const Visualizer: React.FC<VisualizerProps> = ({
  micLevel,
  agentAudioLevel,
  isVoiceMode,
  isPlayingAudio,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const width = canvas.width;
      const height = canvas.height;
      const centerY = height / 2;

      const isAgentActive = isPlayingAudio;
      const isUserActive = isVoiceMode && micLevel > 0.05;
      const activeLevel = isAgentActive
        ? Math.max(0.2, agentAudioLevel * 2.5)
        : isUserActive
        ? Math.max(0.2, micLevel * 2)
        : 0.05;

      const numBars = 36;
      const barWidth = 4;
      const gap = (width - numBars * barWidth) / (numBars + 1);

      phase += 0.08;

      for (let i = 0; i < numBars; i++) {
        const x = gap + i * (barWidth + gap);
        const wave = Math.sin(phase + (i * 0.3)) * Math.cos(phase * 0.5 + (i * 0.2));
        const amplitude = (height * 0.42) * activeLevel * Math.abs(wave) + 4;

        const gradient = ctx.createLinearGradient(0, centerY - amplitude, 0, centerY + amplitude);
        if (isAgentActive) {
          gradient.addColorStop(0, '#818cf8');
          gradient.addColorStop(0.5, '#c084fc');
          gradient.addColorStop(1, '#6366f1');
        } else if (isUserActive) {
          gradient.addColorStop(0, '#34d399');
          gradient.addColorStop(0.5, '#10b981');
          gradient.addColorStop(1, '#059669');
        } else {
          gradient.addColorStop(0, '#334155');
          gradient.addColorStop(1, '#1e293b');
        }

        ctx.fillStyle = gradient;
        ctx.beginPath();
        const barHeight = Math.max(6, amplitude * 2);
        const topY = centerY - barHeight / 2;
        ctx.roundRect(x, topY, barWidth, barHeight, 3);
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [micLevel, agentAudioLevel, isVoiceMode, isPlayingAudio]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        backgroundColor: 'rgba(15, 23, 42, 0.5)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
      }}
    >
      <canvas
        ref={canvasRef}
        width={400}
        height={76}
        style={{
          width: '100%',
          maxWidth: '380px',
          height: '76px',
          borderRadius: '12px',
          backgroundColor: 'rgba(5, 8, 16, 0.6)',
        }}
      />
      <div
        style={{
          marginTop: '10px',
          fontSize: '0.72rem',
          fontFamily: 'var(--font-mono)',
          fontWeight: 600,
          letterSpacing: '0.05em',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          color: isPlayingAudio ? '#a5b4fc' : isVoiceMode ? '#34d399' : '#64748b',
        }}
      >
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isPlayingAudio ? '#818cf8' : isVoiceMode ? '#10b981' : '#475569',
            boxShadow: isPlayingAudio || isVoiceMode ? '0 0 10px currentColor' : 'none',
          }}
        />
        {isPlayingAudio
          ? 'AGENT TRANSMITTING (24 kHz PCM)'
          : isVoiceMode
          ? 'LISTENING TO MICROPHONE (16 kHz PCM)'
          : 'STANDBY • READY FOR VOICE OR TEXT'}
      </div>
    </div>
  );
};
