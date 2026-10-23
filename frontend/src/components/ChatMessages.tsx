import React, { useEffect, useRef } from 'react';
import { User, Bot, Trash2, Mic, MessageSquare } from 'lucide-react';
import { ChatMessage } from '../types/events';

interface ChatMessagesProps {
  messages: ChatMessage[];
  onClear: () => void;
  onSelectPrompt: (prompt: string) => void;
  isConnected: boolean;
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  onClear,
  onSelectPrompt,
  isConnected,
}) => {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const starterPrompts = [
    'How does Gemini Live bidirectional streaming work?',
    'Explain quantum computing in simple Hinglish.',
    'What are the key benefits of real-time AudioWorklet processing?',
    'Namaste! Kaise ho aap? Aaj ka weather update batao.',
  ];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        overflow: 'hidden',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 20px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          backgroundColor: 'rgba(10, 15, 30, 0.5)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <MessageSquare size={16} style={{ color: '#818cf8' }} />
          <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f1f5f9' }}>
            Live Conversation Transcript
          </span>
          <span
            style={{
              fontSize: '0.72rem',
              padding: '2px 8px',
              borderRadius: '9999px',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              color: '#94a3b8',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {messages.length} turns
          </span>
        </div>

        {messages.length > 0 && (
          <button
            onClick={onClear}
            className="btn btn-ghost"
            style={{ padding: '6px 12px', fontSize: '0.75rem', color: '#94a3b8' }}
            title="Clear transcripts"
          >
            <Trash2 size={13} />
            <span>Clear</span>
          </button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div
        style={{
          flex: 1,
          padding: '20px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
        }}
      >
        {messages.length === 0 ? (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
              color: '#94a3b8',
              padding: '20px',
            }}
          >
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '16px',
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#818cf8',
                marginBottom: '14px',
              }}
            >
              <Bot size={24} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#f1f5f9', marginBottom: '6px' }}>
              Real-Time Conversational AI
            </h3>
            <p style={{ fontSize: '0.82rem', maxWidth: '420px', lineHeight: 1.5, marginBottom: '24px' }}>
              Speak through your microphone or type a question in English, Hindi, or Hinglish.
              The model synthesizes speech and text in real-time.
            </p>

            {/* Quick Starters */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '10px',
                width: '100%',
                maxWidth: '520px',
              }}
            >
              {starterPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => onSelectPrompt(prompt)}
                  disabled={!isConnected}
                  style={{
                    padding: '12px 14px',
                    fontSize: '0.78rem',
                    textAlign: 'left',
                    backgroundColor: 'rgba(30, 41, 59, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '12px',
                    color: '#cbd5e1',
                    cursor: isConnected ? 'pointer' : 'not-allowed',
                    opacity: isConnected ? 1 : 0.4,
                    transition: 'all 0.2s',
                    lineHeight: 1.4,
                  }}
                  onMouseEnter={(e) => {
                    if (isConnected) (e.currentTarget.style.backgroundColor = 'rgba(99, 102, 241, 0.15)');
                  }}
                  onMouseLeave={(e) => {
                    if (isConnected) (e.currentTarget.style.backgroundColor = 'rgba(30, 41, 59, 0.5)');
                  }}
                >
                  “{prompt}”
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  gap: '10px',
                  justifyContent: isUser ? 'flex-end' : 'flex-start',
                }}
              >
                {!isUser && (
                  <div
                    style={{
                      flexShrink: 0,
                      width: '32px',
                      height: '32px',
                      borderRadius: '10px',
                      backgroundColor: 'rgba(99, 102, 241, 0.2)',
                      border: '1px solid rgba(99, 102, 241, 0.35)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#a5b4fc',
                    }}
                  >
                    <Bot size={16} />
                  </div>
                )}

                <div
                  style={{
                    maxWidth: '80%',
                    padding: '12px 16px',
                    borderRadius: '16px',
                    borderTopRightRadius: isUser ? '4px' : '16px',
                    borderTopLeftRadius: !isUser ? '4px' : '16px',
                    backgroundColor: isUser
                      ? 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)'
                      : 'rgba(30, 41, 59, 0.8)',
                    background: isUser
                      ? 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)'
                      : 'rgba(30, 41, 59, 0.85)',
                    border: isUser ? 'none' : '1px solid rgba(255, 255, 255, 0.08)',
                    color: '#f8fafc',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.25)',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '12px',
                      marginBottom: '6px',
                      fontSize: '0.72rem',
                      opacity: 0.8,
                    }}
                  >
                    <span style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                      {isUser ? <User size={12} /> : <Bot size={12} />}
                      {isUser ? 'You' : 'Gemini Live Agent'}
                    </span>
                    {!msg.isFinal && (
                      <span
                        style={{
                          color: '#fde047',
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.68rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                      >
                        ● transcribing
                      </span>
                    )}
                  </div>
                  <p style={{ margin: 0, fontSize: '0.88rem', lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>
                    {msg.text}
                  </p>
                </div>

                {isUser && (
                  <div
                    style={{
                      flexShrink: 0,
                      width: '32px',
                      height: '32px',
                      borderRadius: '10px',
                      backgroundColor: 'rgba(16, 185, 129, 0.2)',
                      border: '1px solid rgba(16, 185, 129, 0.35)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#6ee7b7',
                    }}
                  >
                    <Mic size={15} />
                  </div>
                )}
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
