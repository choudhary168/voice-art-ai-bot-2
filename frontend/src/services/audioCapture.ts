export class AudioCaptureService {
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private processor: ScriptProcessorNode | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private isCapturing: boolean = false;
  private targetSampleRate: number = 16000;
  private chunkDurationMs: number = 100;
  private buffer: number[] = [];
  private onChunkCallback: ((base64Pcm: string, rms: number) => void) | null = null;

  public get isRecording(): boolean {
    return this.isCapturing;
  }

  public async start(onChunk: (base64Pcm: string, rms: number) => void): Promise<void> {
    if (this.isCapturing) return;

    this.onChunkCallback = onChunk;
    this.buffer = [];

    // Request microphone stream with echo cancellation and noise suppression
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    try {
      this.audioContext = new AudioContextClass({ sampleRate: 16000 });
    } catch {
      this.audioContext = new AudioContextClass();
    }

    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }

    this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);
    const bufferSize = 2048;
    this.processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

    // Prevent Chrome V8 Garbage Collection from pausing audio processing
    (window as any).__voiceAgentProcessor = this.processor;
    (window as any).__voiceAgentSource = this.sourceNode;

    const actualSampleRate = this.audioContext.sampleRate;
    const targetChunkSamples = Math.floor((this.targetSampleRate * this.chunkDurationMs) / 1000);

    this.processor.onaudioprocess = (e: AudioProcessingEvent) => {
      if (!this.isCapturing) return;

      const inputChannelData = e.inputBuffer.getChannelData(0);

      // Resample down to 16kHz if browser provides different sample rate (e.g. 44100 or 48000)
      const resampled = this.resampleAudio(inputChannelData, actualSampleRate, this.targetSampleRate);

      for (let i = 0; i < resampled.length; i++) {
        this.buffer.push(resampled[i]);
      }

      // When accumulated samples equal or exceed chunk duration
      while (this.buffer.length >= targetChunkSamples) {
        const chunkSamples = this.buffer.splice(0, targetChunkSamples);
        const { pcmBytes, rms } = this.convertTo16BitPCM(chunkSamples);
        const base64Data = this.bytesToBase64(pcmBytes);

        if (this.onChunkCallback) {
          this.onChunkCallback(base64Data, rms);
        }
      }
    };

    // Keep processor active by connecting to low-gain destination to prevent browser thread freeze
    this.sourceNode.connect(this.processor);
    const silentGain = this.audioContext.createGain();
    silentGain.gain.setValueAtTime(0.0001, this.audioContext.currentTime);
    this.processor.connect(silentGain);
    silentGain.connect(this.audioContext.destination);

    this.isCapturing = true;
  }

  public stop(): void {
    this.isCapturing = false;
    this.buffer = [];

    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }
    if (this.sourceNode) {
      this.sourceNode.disconnect();
      this.sourceNode = null;
    }
    delete (window as any).__voiceAgentProcessor;
    delete (window as any).__voiceAgentSource;

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }
    if (this.audioContext) {
      this.audioContext.close().catch(() => {});
      this.audioContext = null;
    }
  }

  private resampleAudio(input: Float32Array, inRate: number, outRate: number): Float32Array {
    if (inRate === outRate) {
      return input;
    }
    const ratio = inRate / outRate;
    const outLength = Math.round(input.length / ratio);
    const result = new Float32Array(outLength);

    for (let i = 0; i < outLength; i++) {
      const origPos = i * ratio;
      const index = Math.floor(origPos);
      const frac = origPos - index;
      const nextIndex = Math.min(index + 1, input.length - 1);
      result[i] = input[index] * (1 - frac) + input[nextIndex] * frac;
    }
    return result;
  }

  private convertTo16BitPCM(samples: number[]): { pcmBytes: Uint8Array; rms: number } {
    const buffer = new ArrayBuffer(samples.length * 2);
    const view = new DataView(buffer);
    let sumSquares = 0;

    for (let i = 0; i < samples.length; i++) {
      // Clamp between -1.0 and 1.0
      const s = Math.max(-1, Math.min(1, samples[i]));
      sumSquares += s * s;
      // Convert to 16-bit signed integer
      const int16 = s < 0 ? s * 0x8000 : s * 0x7fff;
      view.setInt16(i * 2, int16, true); // Little endian
    }

    const rms = Math.sqrt(sumSquares / (samples.length || 1));
    return { pcmBytes: new Uint8Array(buffer), rms };
  }

  private bytesToBase64(bytes: Uint8Array): string {
    let binary = '';
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }
}

export const audioCaptureService = new AudioCaptureService();
