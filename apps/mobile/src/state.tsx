import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { ApiError, KathaClient } from "./api/client";

// Dev default; Android emulators reach the host machine via 10.0.2.2.
const DEFAULT_BASE_URL = "http://localhost:8000";
const STORAGE_KEY = "katha.session.v1";

interface StoredSession {
  baseUrl: string;
  token: string;
  email: string;
}

interface AppState {
  ready: boolean;
  client: KathaClient | null;
  signIn: (baseUrl: string, email: string, name: string, familyName: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const Ctx = createContext<AppState>({
  ready: false,
  client: null,
  signIn: async () => {},
  signOut: async () => {},
});

export function AppStateProvider({ children }: { children: React.ReactNode }) {
  const [client, setClient] = useState<KathaClient | null>(null);
  const [ready, setReady] = useState(false);

  // Restore a persisted session on boot; drop it if the token went stale
  // (e.g. the dev database was reset).
  useEffect(() => {
    void (async () => {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEY);
        if (raw) {
          const stored = JSON.parse(raw) as StoredSession;
          const c = new KathaClient(stored.baseUrl, stored.token);
          await c.listStorytellers(); // validates the token
          setClient(c);
        }
      } catch {
        await AsyncStorage.removeItem(STORAGE_KEY);
      } finally {
        setReady(true);
      }
    })();
  }, []);

  const value = useMemo<AppState>(
    () => ({
      ready,
      client,
      signIn: async (baseUrl, email, name, familyName) => {
        const url = baseUrl || DEFAULT_BASE_URL;
        const c = new KathaClient(url);
        let token: string;
        try {
          token = await c.signup(email, name, familyName);
        } catch (e) {
          // Returning keeper: email already registered -> log in instead.
          if (e instanceof ApiError && e.status === 409) token = await c.login(email);
          else throw e;
        }
        await AsyncStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({ baseUrl: url, token, email } satisfies StoredSession),
        );
        setClient(c);
      },
      signOut: async () => {
        await AsyncStorage.removeItem(STORAGE_KEY);
        setClient(null);
      },
    }),
    [client, ready],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useApp = () => useContext(Ctx);
export { DEFAULT_BASE_URL };
