export const SOCIAL_CORE_URL =
  process.env.NEXT_PUBLIC_SOCIAL_URL ||
  process.env.NEXT_PUBLIC_CORE_URL ||
  "http://127.0.0.1:8103";

export type PlatformType = "youtube" | "tiktok" | "facebook" | "instagram" | "douyin" | "threads" | "x";
export type PostStatus = "draft" | "pending_approval" | "approved" | "scheduled" | "publishing" | "published" | "failed" | "cancelled";

export interface PostingWindow {
  weekday: number;
  start: string;
  end: string;
}

export interface AccountAuth {
  mode: "oauth" | "manual" | "browser_assisted";
  token_ref?: string | null;
  scopes?: string[];
  expires_at?: string | null;
}

export interface SocialAccount {
  id: string;
  platform: PlatformType;
  handle: string;
  display_name: string;
  avatar?: string;
  channel_url?: string;
  auth: AccountAuth;
  status: "connected" | "expired" | "manual" | "disabled";
  default_hashtags: string[];
  default_caption_footer: string;
  posting_windows: PostingWindow[];
  daily_limit: number;
  tags?: string[];
}

export interface PostMedia {
  path: string;
  platform_variant?: string | null;
  kind: "video" | "image" | "carousel";
  duration_s: number;
  thumb?: string;
}

export interface PostTarget {
  id: string;
  account_id: string;
  platform: PlatformType;
  scheduled_at?: string | null;
  caption: string;
  hashtags: string[];
  title?: string;
  description?: string;
  tags?: string[];
  privacy?: "public" | "unlisted" | "private";
  made_for_kids?: boolean;
  cover_time_s?: number;
  first_comment?: string;
  product_link?: string;
  disclosure_ad?: boolean;
  status: PostStatus;
  external_id?: string | null;
  external_url?: string | null;
  attempts?: number;
  last_error?: string | null;
  published_at?: string | null;
}

export interface PostApproval {
  required: boolean;
  by?: string | null;
  at?: string | null;
  note?: string | null;
}

export interface Post {
  id: string;
  project_id: string;
  title: string;
  media: PostMedia[];
  source_ref?: string | null;
  render_job_id?: string | null;
  idea_id?: string | null;
  status: PostStatus;
  approval: PostApproval;
  targets: PostTarget[];
  created_at: string;
  updated_at: string;
}

export interface RecurringSlot {
  id: string;
  account_id: string;
  rrule: string;
  label?: string;
  template_hint?: string | null;
}

export interface CalendarNote {
  id: string;
  date: string;
  text: string;
  color?: string;
}

export interface CalendarItem {
  post_id: string;
  target_id: string;
  title: string;
  platform: PlatformType;
  account_id: string;
  account_name: string;
  scheduled_at?: string | null;
  status: PostStatus;
  caption: string;
  thumb?: string;
}

export interface EmptySlot {
  account_id: string;
  platform: PlatformType;
  weekday: number;
  start: string;
  end: string;
  label: string;
}

export interface CalendarResponse {
  view: "month" | "week" | "agenda";
  from?: string;
  to?: string;
  items: CalendarItem[];
  empty_slots: EmptySlot[];
  notes: CalendarNote[];
  slots: RecurringSlot[];
}

// ==========================================
// API Helpers
// ==========================================

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API Error [${res.status}]: ${errorText}`);
  }
  return res.json();
}

export const socialApi = {
  // Accounts
  listAccounts: (projectId: string) =>
    fetchJson<SocialAccount[]>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/accounts`),

  createAccount: (projectId: string, account: Partial<SocialAccount>) =>
    fetchJson<SocialAccount>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/accounts`, {
      method: "POST",
      body: JSON.stringify(account),
    }),

  updateAccount: (projectId: string, accountId: string, account: Partial<SocialAccount>) =>
    fetchJson<SocialAccount>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/accounts/${accountId}`, {
      method: "PUT",
      body: JSON.stringify(account),
    }),

  deleteAccount: (projectId: string, accountId: string) =>
    fetchJson<{ status: string; account_id: string }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/accounts/${accountId}`,
      { method: "DELETE" }
    ),

  // Posts
  listPosts: (projectId: string, params?: Record<string, string>) => {
    const query = new URLSearchParams(params || {}).toString();
    return fetchJson<Post[]>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/posts?${query}`);
  },

  getPost: (projectId: string, postId: string) =>
    fetchJson<Post>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}`),

  createPost: (projectId: string, post: Partial<Post>) =>
    fetchJson<Post>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/posts`, {
      method: "POST",
      body: JSON.stringify(post),
    }),

  createDraftPost: (projectId: string, data: { media_path?: string; title: string; caption?: string; platforms: string[] }) =>
    fetchJson<Post>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/draft`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updatePost: (projectId: string, postId: string, patch: Partial<Post>) =>
    fetchJson<Post>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),

  deletePost: (projectId: string, postId: string) =>
    fetchJson<{ status: string; post_id: string }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}`,
      { method: "DELETE" }
    ),

  submitPost: (projectId: string, postId: string, note?: string) =>
    fetchJson<Post>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}/submit`, {
      method: "POST",
      body: JSON.stringify({ actor: "user", note: note || "" }),
    }),

  approvePost: (projectId: string, postId: string, note?: string) =>
    fetchJson<Post>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}/approve`, {
      method: "POST",
      body: JSON.stringify({ actor: "user", note: note || "" }),
    }),

  rejectPost: (projectId: string, postId: string, reason?: string) =>
    fetchJson<Post>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}/reject`, {
      method: "POST",
      body: JSON.stringify({ actor: "user", reason: reason || "" }),
    }),

  schedulePost: (projectId: string, postId: string, targets: Record<string, string>) =>
    fetchJson<Post>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}/schedule`, {
      method: "POST",
      body: JSON.stringify({ targets, actor: "user" }),
    }),

  updateTargetTime: (projectId: string, postId: string, targetId: string, time: string) =>
    fetchJson<Post>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}/targets/${targetId}/time`, {
      method: "PUT",
      body: JSON.stringify({ time, actor: "user" }),
    }),

  cancelPost: (projectId: string, postId: string) =>
    fetchJson<Post>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}/cancel`, {
      method: "POST",
      body: JSON.stringify({ actor: "user" }),
    }),

  duplicatePost: (projectId: string, postId: string) =>
    fetchJson<Post>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}/duplicate`, {
      method: "POST",
      body: JSON.stringify({ actor: "user" }),
    }),

  // Calendar
  getCalendar: (projectId: string, params?: { from?: string; to?: string; view?: string }) => {
    const query = new URLSearchParams(params as Record<string, string> || {}).toString();
    return fetchJson<CalendarResponse>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/calendar?${query}`);
  },

  // Slots & Notes
  listSlots: (projectId: string, accountId?: string) =>
    fetchJson<RecurringSlot[]>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/slots${accountId ? `?account_id=${accountId}` : ""}`
    ),

  saveSlots: (projectId: string, slots: RecurringSlot[]) =>
    fetchJson<RecurringSlot[]>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/slots`, {
      method: "PUT",
      body: JSON.stringify(slots),
    }),

  listNotes: (projectId: string, from?: string, to?: string) => {
    const query = new URLSearchParams({ ...(from ? { from } : {}), ...(to ? { to } : {}) }).toString();
    return fetchJson<CalendarNote[]>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/notes?${query}`);
  },

  saveNotes: (projectId: string, notes: CalendarNote[]) =>
    fetchJson<CalendarNote[]>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/notes`, {
      method: "PUT",
      body: JSON.stringify(notes),
    }),

  // Helpers
  suggestTime: (projectId: string, accountId: string, after?: string) =>
    fetchJson<{ account_id: string; suggested_time: string }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/suggest-time`,
      {
        method: "POST",
        body: JSON.stringify({ account_id: accountId, after }),
      }
    ),

  generateCaptionVariants: (
    projectId: string,
    data: {
      title: string;
      caption: string;
      hashtags: string[];
      platforms: string[];
      product_link?: string;
      footer?: string;
    }
  ) =>
    fetchJson<{ variants: Record<string, any> }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/caption-variants`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  // Scheduler & Publishing
  getSchedulerStatus: (projectId: string) =>
    fetchJson<{ heartbeat: string | null; scheduled_count: number; recent_activity: any[] }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/scheduler/status`
    ),

  validateTarget: (projectId: string, postId: string, targetId: string) =>
    fetchJson<{ target_id: string; issues: { level: string; code: string; message: string }[] }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}/targets/${targetId}/validate`,
      { method: "POST" }
    ),

  publishNow: (projectId: string, postId: string) =>
    fetchJson<{ post_id: string; status: string; targets: any[] }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}/publish-now`,
      { method: "POST" }
    ),

  markPublished: (projectId: string, postId: string, targetId: string, url: string) =>
    fetchJson<{ post_id: string; target_id: string; status: string; url: string }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/posts/${postId}/targets/${targetId}/mark-published`,
      {
        method: "POST",
        body: JSON.stringify({ url }),
      }
    ),

  getConnectUrl: (projectId: string, accountId: string) =>
    fetchJson<{ account_id: string; platform: string; connect_url: string }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/accounts/${accountId}/connect`
    ),

  refreshAccount: (projectId: string, accountId: string) =>
    fetchJson<{ status: string; details: any }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/accounts/${accountId}/refresh`,
      { method: "POST" }
    ),

  getPackageZipUrl: (projectId: string, postId: string, platform: string) =>
    `${SOCIAL_CORE_URL}/projects/${projectId}/social/packages/${postId}/${platform}.zip`,
};
