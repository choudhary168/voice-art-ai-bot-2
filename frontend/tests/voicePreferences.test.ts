import assert from 'node:assert/strict';
import test from 'node:test';
import { DEFAULT_VOICE, VOICE_PREFERENCE_KEY, loadVoicePreference, saveVoicePreference } from '../src/config/voices.ts';

function memoryStorage(initial?: string) {
  const values = new Map<string, string>();
  if (initial !== undefined) values.set(VOICE_PREFERENCE_KEY, initial);
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
  };
}

test('voice selection persists and is restored from storage', () => {
  const storage = memoryStorage();
  assert.equal(saveVoicePreference('Aoede', storage), 'Aoede');
  assert.equal(loadVoicePreference(storage), 'Aoede');
});

test('missing or unsupported stored voice falls back to Puck', () => {
  assert.equal(loadVoicePreference(memoryStorage()), DEFAULT_VOICE);
  assert.equal(loadVoicePreference(memoryStorage('arbitrary-value')), DEFAULT_VOICE);
  const storage = memoryStorage();
  assert.equal(saveVoicePreference('arbitrary-value', storage), DEFAULT_VOICE);
  assert.equal(loadVoicePreference(storage), DEFAULT_VOICE);
});

test('storage failures do not prevent a default voice from being used', () => {
  const brokenStorage = {
    getItem: () => { throw new Error('storage blocked'); },
    setItem: () => { throw new Error('storage blocked'); },
  };
  assert.equal(loadVoicePreference(brokenStorage), DEFAULT_VOICE);
  assert.equal(saveVoicePreference('Aoede', brokenStorage), 'Aoede');
});
