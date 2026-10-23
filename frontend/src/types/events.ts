export type ClientEventType =
  | 'session.start'
  | 'audio.chunk'
  | 'audio.end'
  | 'text.message'
  | 'response.interrupt'
  | 'session.stop';

export type ServerEventType =
  | 'session.ready'
  | 'transcript.input'
  | 'transcript.output'
  | 'audio.chunk'
  | 'response.started'
  | 'response.completed'
  | 'session.error'
  | 'session.closed';

export interface LatencyMetrics {
  client_session_start?: number;
  gemini_connected?: number;
  first_input_sent?: number;
  first_input_transcription?: number;
  first_model_response?: number;
  first_output_transcription?: number;
  first_audio_chunk?: number;
  turn_completed?: number;
  e2e_first_audio_ms?: number;
  e2e_first_transcription_ms?: number;
  total_turn_duration_ms?: number;
}

export interface SessionReadyPayload {
  session_id: string;
  model: string;
  voice: string;
  input_sample_rate: number;
  output_sample_rate: number;
  channels: number;
  bits_per_sample: number;
  capabilities: string[];
}

export interface TranscriptInputPayload {
  text: string;
  is_final: boolean;
  timestamp: number;
}

export interface TranscriptOutputPayload {
  text: string;
  is_final: boolean;
  turn_id: string;
  timestamp: number;
}

export interface ServerAudioChunkPayload {
  data: string; // Base64 PCM 24kHz
  seq: number;
  turn_id: string;
  sample_rate: number;
  timestamp: number;
}

export interface ResponseStartedPayload {
  turn_id: string;
  timestamp: number;
}

export interface ResponseCompletedPayload {
  turn_id: string;
  timestamp: number;
  metrics: LatencyMetrics;
}

export interface SessionErrorPayload {
  code: string;
  message: string;
  recoverable: boolean;
  timestamp: number;
}

export interface SessionClosedPayload {
  reason: string;
  timestamp: number;
}

export interface ServerEvent {
  type: ServerEventType;
  payload: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  text: string;
  timestamp: number;
  isFinal?: boolean;
  turnId?: string;
}

export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';
