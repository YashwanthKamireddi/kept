import React, { createContext, useContext, useMemo, useState } from "react";
import { KathaClient } from "./api/client";

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
        await c.signup(email, name, familyName);
        setClient(c);
      },
    }),
    [client],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useApp = () => useContext(Ctx);
export { DEFAULT_BASE_URL };
