import { useCallback, useEffect, useRef, useState } from 'react';
import { audioCaptureService } from '../services/audioCapture';
import { audioPlaybackService } from '../services/audioPlayback';
import { wsService } from '../services/websocket';
import { LiveVoiceName, loadVoicePreference, saveVoicePreference } from '../config/voices';
import {
  ChatMessage,
  ConnectionState,
  LatencyMetrics,
  ServerAudioChunkPayload,
  ServerEvent,
  SessionReadyPayload,
  TranscriptInputPayload,
  TranscriptOutputPayload,
} from '../types/events';

export function useVoiceAgent() {
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [sessionInfo, setSessionInfo] = useState<SessionReadyPayload | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isVoiceMode, setIsVoiceMode] = useState<boolean>(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [micLevel, setMicLevel] = useState<number>(0);
  const [agentAudioLevel, setAgentAudioLevel] = useState<number>(0);
  const [latencyMetrics, setLatencyMetrics] = useState<LatencyMetrics | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedVoice, setSelectedVoice] = useState<LiveVoiceName>(() => loadVoicePreference());

  // Reference to keep track of active turn without state closure staleness
  const currentTurnIdRef = useRef<string | null>(null);

  // Bind audio playback state callbacks
  useEffect(() => {
    audioPlaybackService.setCallbacks(
      (playing) => setIsPlayingAudio(playing),
      (level) => setAgentAudioLevel(level)
    );
  }, []);

  // Handle incoming server events
  useEffect(() => {
    const unbind = wsService.on('*', (event: ServerEvent) => {
      switch (event.type) {
        case 'session.ready': {
          const payload = event.payload as SessionReadyPayload;
          if (payload.session_id) {
            setSessionInfo(payload);
            setConnectionState('connected');
            setErrorMessage(null);
          }
          break;
        }

        case 'transcript.input': {
          const payload = event.payload as TranscriptInputPayload;
          if (!payload.text) return;

          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.role === 'user' && !last.isFinal) {
              // Update interim transcript
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...last,
                text: payload.text,
                isFinal: payload.is_final,
              };
              return updated;
            } else {
              // Append new user speech turn
              return [
                ...prev,
                {
                  id: `user-${Date.now()}`,
                  role: 'user',
                  text: payload.text,
                  timestamp: payload.timestamp || Date.now(),
                  isFinal: payload.is_final,
                },
              ];
            }
          });
          break;
        }

        case 'response.started': {
          const turnId = event.payload.turn_id;
          currentTurnIdRef.current = turnId;
          break;
        }

        case 'transcript.output': {
          const payload = event.payload as TranscriptOutputPayload;
          if (!payload.text) return;

          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.role === 'agent' && last.turnId === payload.turn_id) {
              // Append text to current agent turn
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...last,
                text: payload.text.startsWith(last.text) ? payload.text : `${last.text} ${payload.text}`.trim(),
                isFinal: payload.is_final,
              };
              return updated;
            } else {
              // New agent message turn
              return [
                ...prev,
                {
                  id: `agent-${payload.turn_id || Date.now()}`,
                  role: 'agent',
                  text: payload.text,
                  timestamp: payload.timestamp || Date.now(),
                  isFinal: payload.is_final,
                  turnId: payload.turn_id,
                },
              ];
            }
          });
          break;
        }

        case 'audio.chunk': {
          const payload = event.payload as ServerAudioChunkPayload;
          if (payload.data) {
            audioPlaybackService.enqueueChunk(payload.data, payload.sample_rate);
          }
          break;
        }

        case 'response.completed': {
          if (event.payload.metrics) {
            setLatencyMetrics(event.payload.metrics);
          }
          break;
        }

        case 'session.error': {
          setErrorMessage(event.payload.message || 'An error occurred.');
          break;
        }

        case 'session.closed': {
          setConnectionState('disconnected');
          setIsVoiceMode(false);
          audioCaptureService.stop();
          audioPlaybackService.interrupt();
          break;
        }

        default:
          break;
      }
    });

    return () => unbind();
  }, []);

  // Connect to Gemini Live session
  const connect = useCallback(async (systemInstruction?: string, voiceName?: string) => {
    let unbind: (() => void) | undefined;
    let readyTimer: number | undefined;
    try {
      setConnectionState('connecting');
      setErrorMessage(null);
      // The greeting is streamed after session setup; initialize Web Audio while
      // this connect call is still running from the user's click gesture.
      audioPlaybackService.unlock();
      await wsService.connect();

      // Wait until the backend has finished opening the Gemini Live session.
      // A WebSocket being open does not mean it is ready to accept audio yet.
      const sessionReady = new Promise<void>((resolve, reject) => {
        readyTimer = window.setTimeout(() => {
          unbind?.();
          reject(new Error('Timed out while connecting to the Gemini Live session.'));
        }, 30000);
        unbind = wsService.on('*', (event: ServerEvent) => {
          if (event.type === 'session.ready' && event.payload.session_id) {
            window.clearTimeout(readyTimer);
            unbind?.();
            resolve();
          } else if (event.type === 'session.error') {
            window.clearTimeout(readyTimer);
            unbind?.();
            reject(new Error(event.payload.message || 'Failed to start Gemini Live session.'));
          }
        });
      });

      // Emit session.start
      wsService.send('session.start', {
        system_instruction: systemInstruction,
        voice_name: voiceName ?? selectedVoice,
        client_timestamp: Date.now() / 1000,
      });
      await sessionReady;
      return true;
    } catch (err: any) {
      console.error('Connection failed:', err);
      setConnectionState('error');
      setErrorMessage(err.message || 'Failed to connect to backend server.');
      return false;
    } finally {
      if (readyTimer !== undefined) window.clearTimeout(readyTimer);
      unbind?.();
    }
  }, [selectedVoice]);

  const updateSelectedVoice = useCallback((voice: LiveVoiceName) => {
    setSelectedVoice(saveVoicePreference(voice));
  }, []);

  // Disconnect session
  const disconnect = useCallback(() => {
    if (isVoiceMode) {
      audioCaptureService.stop();
      setIsVoiceMode(false);
    }
    audioPlaybackService.interrupt();
    wsService.disconnect('user_initiated');
    setConnectionState('disconnected');
  }, [isVoiceMode]);

  // Toggle microphone continuous streaming
  const toggleVoiceMode = useCallback(async () => {
    if (isVoiceMode) {
      audioCaptureService.stop();
      wsService.send('audio.end', { timestamp: Date.now() / 1000 });
      setIsVoiceMode(false);
      setMicLevel(0);
      return;
    }

    try {
      if (!wsService.isConnected) {
        const connected = await connect();
        if (!connected) return;
      }

      let seq = 0;
      await audioCaptureService.start((base64Chunk, rms) => {
        seq++;
        setMicLevel(Math.min(1, rms * 8)); // Scaled for visualizer
        wsService.send('audio.chunk', {
          data: base64Chunk,
          seq,
          sample_rate: 16000,
          timestamp: Date.now() / 1000,
        });
      });
      setIsVoiceMode(true);
      setErrorMessage(null);
    } catch (err: any) {
      console.error('Microphone access denied or failed:', err);
      setErrorMessage(`Microphone error: ${err.message || 'Permission denied'}`);
    }
  }, [isVoiceMode, connect]);

  // Send typed text message
  const sendTextMessage = useCallback((text: string) => {
    if (!text.trim() || !wsService.isConnected) return;

    // Immediately record in message history
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: text.trim(),
      timestamp: Date.now() / 1000,
      isFinal: true,
    };
    setMessages((prev) => [...prev, userMsg]);

    wsService.send('text.message', {
      text: text.trim(),
      timestamp: Date.now() / 1000,
    });
  }, []);

  // Interrupt response
  const interrupt = useCallback(() => {
    audioPlaybackService.interrupt();
    wsService.send('response.interrupt', {
      turn_id: currentTurnIdRef.current || undefined,
      timestamp: Date.now() / 1000,
    });
  }, []);

  // Toggle mute
  const toggleMute = useCallback(() => {
    setIsMuted((prev) => {
      const next = !prev;
      audioPlaybackService.setMute(next);
      return next;
    });
  }, []);

  // Clear chat history
  const clearChat = useCallback(() => {
    setMessages([]);
  }, []);

  return {
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
    setSelectedVoice: updateSelectedVoice,
    connect,
    disconnect,
    toggleVoiceMode,
    sendTextMessage,
    interrupt,
    toggleMute,
    clearChat,
  };
}
