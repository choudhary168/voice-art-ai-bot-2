export const DEFAULT_VOICE = 'Puck';
export const VOICE_PREFERENCE_KEY = 'gemini-live-voice';

export const LIVE_VOICES = [
  { name: 'Zephyr', style: 'Bright' },
  { name: 'Puck', style: 'Upbeat' },
  { name: 'Charon', style: 'Informative' },
  { name: 'Kore', style: 'Firm' },
  { name: 'Fenrir', style: 'Excitable' },
  { name: 'Leda', style: 'Youthful' },
  { name: 'Orus', style: 'Firm' },
  { name: 'Aoede', style: 'Breezy' },
  { name: 'Callirrhoe', style: 'Easy-going' },
  { name: 'Autonoe', style: 'Bright' },
  { name: 'Enceladus', style: 'Breathy' },
  { name: 'Iapetus', style: 'Clear' },
  { name: 'Umbriel', style: 'Easy-going' },
  { name: 'Algieba', style: 'Smooth' },
  { name: 'Despina', style: 'Smooth' },
  { name: 'Erinome', style: 'Clear' },
  { name: 'Algenib', style: 'Gravelly' },
  { name: 'Rasalgethi', style: 'Informative' },
  { name: 'Laomedeia', style: 'Upbeat' },
  { name: 'Achernar', style: 'Soft' },
  { name: 'Alnilam', style: 'Firm' },
  { name: 'Schedar', style: 'Even' },
  { name: 'Gacrux', style: 'Mature' },
  { name: 'Pulcherrima', style: 'Forward' },
  { name: 'Achird', style: 'Friendly' },
  { name: 'Zubenelgenubi', style: 'Casual' },
  { name: 'Vindemiatrix', style: 'Gentle' },
  { name: 'Sadachbia', style: 'Lively' },
  { name: 'Sadaltager', style: 'Knowledgeable' },
  { name: 'Sulafat', style: 'Warm' },
] as const;

export type LiveVoiceName = (typeof LIVE_VOICES)[number]['name'];
export const isLiveVoiceName = (value: unknown): value is LiveVoiceName =>
  typeof value === 'string' && LIVE_VOICES.some((voice) => voice.name === value);

type StorageLike = Pick<Storage, 'getItem' | 'setItem'>;

function browserStorage(): StorageLike | undefined {
  try {
    return window.localStorage;
  } catch {
    return undefined;
  }
}

export function loadVoicePreference(storage?: StorageLike): LiveVoiceName {
  try {
    const value = (storage ?? browserStorage())?.getItem(VOICE_PREFERENCE_KEY);
    return isLiveVoiceName(value) ? value : DEFAULT_VOICE;
  } catch {
    return DEFAULT_VOICE;
  }
}

export function saveVoicePreference(value: unknown, storage?: StorageLike): LiveVoiceName {
  const voice = isLiveVoiceName(value) ? value : DEFAULT_VOICE;
  try {
    (storage ?? browserStorage())?.setItem(VOICE_PREFERENCE_KEY, voice);
  } catch {
    // Private browsing or disabled storage should not prevent session startup.
  }
  return voice;
}
