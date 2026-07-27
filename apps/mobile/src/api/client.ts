/** Typed client for the Katha server API (mirrors apps/server schemas.py). */

export type ConsentStatus = "pending" | "granted" | "declined" | "revoked";

export interface Storyteller {
  id: string;
  name: string;
  address_as: string;
  phone_e164: string;
  language: string;
  timezone: string;
  consent: ConsentStatus;
  life_brief_version: number;
  next_call_at: string | null;
  cadence_days: number;
  created_at: string;
}

export interface Session {
  id: string;
  status: string;
  scheduled_at: string | null;
  started_at: string | null;
  duration_seconds: number;
  audio_key: string;
}

export interface Anchor {
  segment_id: string;
  session_id: string;
  audio_key: string;
  t_start_ms: number;
  t_end_ms: number;
}

export interface Sentence {
  text: string;
  bridge: boolean;
  anchors: Anchor[];
}

export interface Segment {
  id: string;
  idx: number;
  speaker: "storyteller" | "biographer";
  t_start_ms: number;
  t_end_ms: number;
  text: string;
}

export interface SessionDetail extends Session {
  segments: Segment[];
}

export interface FollowUp {
  id: string;
  question: string;
  rationale: string;
  priority: number;
  status: "pending" | "asked" | "retired";
  asked_by_name: string | null;
}

export interface Chapter {
  id: string;
  ordinal: number;
  version: number;
  title: string;
  status: "draft" | "verified" | "published";
  created_at: string;
}

export interface ChapterDetail extends Chapter {
  paragraphs: Sentence[][];
}

export interface MemoirChapter {
  ordinal: number;
  title: string;
  paragraphs: Sentence[][];
}

export interface Memoir {
  name: string;
  chapters: MemoirChapter[];
}

export interface SearchChapterHit {
  chapter_id: string;
  ordinal: number;
  title: string;
  snippet: string;
}

export interface SearchMomentHit {
  session_id: string;
  started_at: string | null;
  snippet: string;
}

export interface SearchResults {
  query: string;
  chapters: SearchChapterHit[];
  moments: SearchMomentHit[];
}

export interface Portrait {
  name: string;
  life_brief: string; // markdown built by the pipeline
  life_brief_version: number;
}

export interface LifeMoment {
  quote: string;
  anchor: Anchor | null;
}

export interface LifeEntity {
  name: string;
  summary: string;
  moments: LifeMoment[];
}

export interface LifeGroup {
  kind: string;
  label: string;
  entities: LifeEntity[];
}

export interface Life {
  name: string;
  groups: LifeGroup[];
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export class KathaClient {
  constructor(
    public baseUrl: string,
    private token: string | null = null,
  ) {}

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!res.ok) {
      const detail = await res
        .json()
        .then((j) => j.detail ?? res.statusText)
        .catch(() => res.statusText);
      throw new ApiError(res.status, String(detail));
    }
    return (await res.json()) as T;
  }

  async signup(email: string, name: string, familyName: string): Promise<string> {
    const out = await this.request<{ token: string }>("POST", "/auth/signup", {
      email,
      name,
      family_name: familyName,
    });
    this.token = out.token;
    return out.token;
  }

  async login(email: string): Promise<string> {
    const out = await this.request<{ token: string }>("POST", "/auth/login", { email });
    this.token = out.token;
    return out.token;
  }

  listStorytellers = () => this.request<Storyteller[]>("GET", "/storytellers");

  createStoryteller = (input: {
    name: string;
    address_as: string;
    phone_e164: string;
    language?: string;
    timezone?: string;
    next_call_at?: string; // ISO datetime of the first call
    cadence_days?: number;
  }) => this.request<Storyteller>("POST", "/storytellers", input);

  getStoryteller = (storytellerId: string) =>
    this.request<Storyteller>("GET", `/storytellers/${storytellerId}`);

  setConsent = (storytellerId: string, consent: ConsentStatus) =>
    this.request<Storyteller>("PATCH", `/storytellers/${storytellerId}/consent`, {
      consent,
    });

  eraseStoryteller = (storytellerId: string) =>
    this.request<{ erased: boolean }>("DELETE", `/storytellers/${storytellerId}`);

  listSessions = (storytellerId: string) =>
    this.request<Session[]>("GET", `/storytellers/${storytellerId}/sessions`);

  getSession = (sessionId: string) =>
    this.request<SessionDetail>("GET", `/sessions/${sessionId}`);

  listFollowUps = (storytellerId: string) =>
    this.request<FollowUp[]>("GET", `/storytellers/${storytellerId}/follow-ups`);

  retireFollowUp = (followUpId: string) =>
    this.request<FollowUp>("POST", `/follow-ups/${followUpId}/retire`);

  createFollowUp = (storytellerId: string, question: string) =>
    this.request<FollowUp>("POST", `/storytellers/${storytellerId}/follow-ups`, {
      question,
    });

  listChapters = (storytellerId: string) =>
    this.request<Chapter[]>("GET", `/storytellers/${storytellerId}/chapters`);

  getChapter = (chapterId: string) =>
    this.request<ChapterDetail>("GET", `/chapters/${chapterId}`);

  getMemoir = (storytellerId: string) =>
    this.request<Memoir>("GET", `/storytellers/${storytellerId}/memoir`);

  search = (storytellerId: string, q: string) =>
    this.request<SearchResults>(
      "GET",
      `/storytellers/${storytellerId}/search?q=${encodeURIComponent(q)}`,
    );

  getPortrait = (storytellerId: string) =>
    this.request<Portrait>("GET", `/storytellers/${storytellerId}/portrait`);

  getLife = (storytellerId: string) =>
    this.request<Life>("GET", `/storytellers/${storytellerId}/life`);

  /** Short-lived playback URL for a recording (server presigns from R2). */
  resolveAudioUrl = async (audioKey: string): Promise<string | null> => {
    if (!audioKey) return null;
    const path = audioKey.split("/").map(encodeURIComponent).join("/");
    const out = await this.request<{ url: string }>("GET", `/audio/${path}`);
    return out.url;
  };
}
