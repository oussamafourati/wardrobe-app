import * as SecureStore from 'expo-secure-store';

import { apiFetch, statusOf } from '../api/client';

const TOKEN_KEY = 'wardrobe.session.token';

export type SessionInfo = { token: string; userId: string; fresh: boolean };

type Created = { token: string; user_id: string; locale: string };
type Me = { user_id: string; locale: string; created_at: string };

async function createSession(language: string): Promise<SessionInfo> {
  const locale = language.startsWith('en') ? 'en-GB' : 'fr-FR';
  const created = await apiFetch<Created>('/v1/sessions', { method: 'POST', body: { locale } });
  await SecureStore.setItemAsync(TOKEN_KEY, created.token);
  return { token: created.token, userId: created.user_id, fresh: true };
}

async function run(language: string): Promise<SessionInfo> {
  const stored = await SecureStore.getItemAsync(TOKEN_KEY);
  if (!stored) return createSession(language);
  try {
    const me = await apiFetch<Me>('/v1/me', { token: stored });
    return { token: stored, userId: me.user_id, fresh: false };
  } catch (err) {
    // Only a clear "this token is not valid" answer justifies a new identity.
    // A timeout or a network error must never replace the one we have.
    if (statusOf(err) === 401) {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
      return createSession(language);
    }
    throw err;
  }
}

let inflight: Promise<SessionInfo> | null = null;

/** Restores the stored guest session, or creates one. Concurrent calls share one request. */
export function ensureSession(language: string): Promise<SessionInfo> {
  if (!inflight) {
    inflight = run(language).finally(() => {
      inflight = null;
    });
  }
  return inflight;
}
