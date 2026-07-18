import React, { createContext, useContext, useMemo, useState } from "react";
import { ApiError, KathaClient } from "./api/client";

// Dev default; Android emulators reach the host machine via 10.0.2.2.
const DEFAULT_BASE_URL = "http://localhost:8000";

interface AppState {
  client: KathaClient | null;
  signIn: (baseUrl: string, email: string, name: string, familyName: string) => Promise<void>;
}

const Ctx = createContext<AppState>({ client: null, signIn: async () => {} });

export function AppStateProvider({ children }: { children: React.ReactNode }) {
  const [client, setClient] = useState<KathaClient | null>(null);

  const value = useMemo<AppState>(
    () => ({
      client,
      signIn: async (baseUrl, email, name, familyName) => {
        const c = new KathaClient(baseUrl || DEFAULT_BASE_URL);
        try {
          await c.signup(email, name, familyName);
        } catch (e) {
          // Returning keeper: email already registered -> log in instead.
          if (e instanceof ApiError && e.status === 409) await c.login(email);
          else throw e;
        }
        setClient(c);
      },
    }),
    [client],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useApp = () => useContext(Ctx);
export { DEFAULT_BASE_URL };
