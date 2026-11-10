export class AudioPlaybackService {
  private audioContext: AudioContext | null = null;
  private gainNode: GainNode | null = null;
  private nextPlayTime: number = 0;
  private activeSources: Set<AudioBufferSourceNode> = new Set();
  private sampleRate: number = 24000;
  private isMuted: boolean = false;
  private isPlaying: boolean = false;
  private onPlaybackStateChange: ((isPlaying: boolean) => void) | null = null;
  private onAudioLevel: ((rms: number) => void) | null = null;

  constructor(sampleRate: number = 24000) {
    this.sampleRate = sampleRate;
  }

  private initContext(): void {
    if (!this.audioContext || this.audioContext.state === 'closed') {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      this.audioContext = new AudioContextClass({ sampleRate: this.sampleRate });
      this.gainNode = this.audioContext.createGain();
      this.gainNode.gain.value = this.isMuted ? 0 : 1;
      this.gainNode.connect(this.audioContext.destination);
      this.nextPlayTime = 0;
    }

    if (this.audioContext.state === 'suspended') {
      this.audioContext.resume();
    }
  }

  /** Call from a user gesture so later streamed audio can play automatically. */
  public unlock(): void {
    this.initContext();
  }

  public setCallbacks(
    onStateChange: (isPlaying: boolean) => void,
    onLevel: (rms: number) => void
  ): void {
    this.onPlaybackStateChange = onStateChange;
    this.onAudioLevel = onLevel;
  }

  public enqueueChunk(base64Pcm: string, chunkSampleRate?: number): void {
    try {
      this.initContext();
      if (!this.audioContext || !this.gainNode) return;

      const rate = chunkSampleRate || this.sampleRate;
      const float32Samples = this.base64PcmToFloat32(base64Pcm);
      if (float32Samples.length === 0) return;

      // Calculate RMS for visualizer
      let sumSquares = 0;
      for (let i = 0; i < float32Samples.length; i++) {
        sumSquares += float32Samples[i] * float32Samples[i];
      }
      const rms = Math.sqrt(sumSquares / float32Samples.length);
      if (this.onAudioLevel) {
        this.onAudioLevel(rms);
      }

      // Create Web Audio Buffer
      const audioBuffer = this.audioContext.createBuffer(1, float32Samples.length, rate);
      audioBuffer.copyToChannel(float32Samples, 0);

      // Create Source Node
      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(this.gainNode);

      // Exact monotonic scheduling for gapless streaming
      const currentTime = this.audioContext.currentTime;
      const startTime = Math.max(currentTime, this.nextPlayTime);
      source.start(startTime);
      this.nextPlayTime = startTime + audioBuffer.duration;

      this.activeSources.add(source);
      this.updatePlayingState(true);

      source.onended = () => {
        this.activeSources.delete(source);
        if (this.activeSources.size === 0) {
          this.updatePlayingState(false);
          if (this.onAudioLevel) this.onAudioLevel(0);
        }
      };
    } catch (e) {
      console.error('Failed to enqueue and play audio chunk:', e);
    }
  }

  public interrupt(): void {
    // Stop all playing or scheduled sources immediately
    this.activeSources.forEach((source) => {
      try {
        source.stop();
        source.disconnect();
      } catch (_) {}
    });
    this.activeSources.clear();
    this.nextPlayTime = 0;
    this.updatePlayingState(false);
    if (this.onAudioLevel) {
      this.onAudioLevel(0);
    }
  }

  public setMute(muted: boolean): void {
    this.isMuted = muted;
    if (this.gainNode && this.audioContext) {
      const targetGain = muted ? 0 : 1;
      this.gainNode.gain.setValueAtTime(targetGain, this.audioContext.currentTime);
    }
  }

  private updatePlayingState(playing: boolean): void {
    if (this.isPlaying !== playing) {
      this.isPlaying = playing;
      if (this.onPlaybackStateChange) {
        this.onPlaybackStateChange(playing);
      }
    }
  }

  private base64PcmToFloat32(base64: string): Float32Array {
    const binary = window.atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }

    const dataView = new DataView(bytes.buffer);
    const sampleCount = Math.floor(bytes.length / 2);
    const float32 = new Float32Array(sampleCount);

    for (let i = 0; i < sampleCount; i++) {
      const int16 = dataView.getInt16(i * 2, true); // Little endian
      float32[i] = int16 < 0 ? int16 / 32768 : int16 / 32767;
    }

    return float32;
  }
}

export const audioPlaybackService = new AudioPlaybackService(24000);
