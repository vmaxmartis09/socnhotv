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
  auth_mode?: "oauth" | "manual";
  status: "connected" | "expired" | "manual" | "disabled";
  groups?: string[];
  group?: string;
  default_hashtags: string[];
  default_caption_footer: string;
  posting_windows: PostingWindow[];
  golden_windows?: string[];
  daily_limit: number;
  limits?: { daily: number };
  min_gap_minutes?: number;
  color?: string;
  affiliate_default?: { link: string; disclosure: boolean };
  tags?: string[];
}

export interface Issue {
  level: "error" | "warn";
  code: string;
  message_vi: string;
}

export interface PublishableVideo {
  id: string;
  title: string;
  thumb?: string;
  duration_s: number;
  duration_sec?: number;
  width: number;
  height: number;
  size_mb: number;
  aspect_ratio: string;
  variants: Record<string, string>;
  primary_path: string;
  source: "job" | "episode" | "library" | "output";
  posted_count: number;
  last_posted_at?: string | null;
  script_excerpt?: string;
}

export interface PlannedTarget {
  video_id: string;
  video_title: string;
  account_id: string;
  account_name: string;
  platform: PlatformType;
  scheduled_at: string;
  issues: Issue[];
  variant_used?: string | null;
  media_path?: string | null;
}

export interface PlanPreviewRequest {
  video_ids: string[];
  account_ids: string[];
  strategy: "now" | "fixed" | "auto";
  start_at?: string;
  end_at?: string;
  per_day_limit?: number;
  caption_mode?: string;
}

export interface TargetCommitSpec {
  video_id: string;
  account_id: string;
  scheduled_at: string;
  title?: string;
  caption?: string;
  hashtags?: string[];
  privacy?: string;
  made_for_kids?: boolean;
  ai_generated_label?: boolean;
  comment_enabled?: boolean;
  duet_enabled?: boolean;
  stitch_enabled?: boolean;
  first_comment?: string;
  product_link?: string;
  disclosure_ad?: boolean;
}

export interface PlanCommitRequest {
  targets: TargetCommitSpec[];
  approval_required: boolean;
}

export interface PlatformCaptionResult {
  platform: PlatformType;
  account_id?: string;
  account_name?: string;
  hook: string;
  caption: string;
  hashtags: string[];
  cta: string;
  title?: string;
  description?: string;
  tags?: string[];
  disclosure_ad: boolean;
  disclosure_text: string;
}

export interface CaptionGenerateRequest {
  video_id: string;
  platforms: string[];
  tone?: string;
  goal?: string;
  include_affiliate?: boolean;
  affiliate_link?: string;
  vary_per_account?: boolean;
  account_ids?: string[];
}

export interface QueueItem {
  post_id: string;
  target_id: string;
  title: string;
  video_title?: string;
  platform: PlatformType;
  account_id: string;
  account_name: string;
  account_avatar: string;
  scheduled_at?: string | null;
  status: string;
  caption: string;
  thumb: string;
  thumbnail?: string;
  error_message?: string;
  bucket: "draft" | "pending_approval" | "upcoming" | "overdue" | "published" | "failed";
  approval_required: boolean;
  approval_status: "approved" | "pending" | "rejected";
  is_manual: boolean;
  has_package: boolean;
  issues: Issue[];
}

export interface QueueSummary {
  accounts_count: number;
  max_accounts: number;
  draft_count: number;
  pending_approval_count: number;
  overdue_count: number;
  upcoming_count: number;
  published_count: number;
  failed_count: number;
  next_post_time?: string | null;
}

export interface QueueResponse {
  items: QueueItem[];
  summary: QueueSummary;
  total?: number;
  page?: number;
  page_size?: number;
  groups?: Record<string, QueueItem[]>;
}

export interface VideoPostTarget {
  account_id: string;
  platform: PlatformType;
  status: string;
  scheduled_at?: string | null;
  published_url?: string;
  post_id: string;
  target_id: string;
  caption?: string;
  hashtags?: string[];
  title?: string;
  thumb?: string;
  error_message?: string;
}

export interface LibraryVideo extends PublishableVideo {
  posts_by_account: VideoPostTarget[];
}

export interface SocialOverview {
  summary: {
    upcoming_24h_count: number;
    overdue_count: number;
    failed_count: number;
    pending_approval_count: number;
    drafts_count?: number;
    token_expiring_count: number;
    empty_slots_7d_count: number;
  };
  upcoming_24h_count?: number;
  overdue_count?: number;
  failed_count?: number;
  pending_approval_count?: number;
  drafts_count?: number;
  expiring_tokens?: Array<{
    id?: string;
    account_id?: string;
    handle?: string;
    display_name?: string;
    platform: PlatformType;
    expires_at: string;
    days_left?: number;
  }>;
  empty_slots?: Array<{
    date: string;
    weekday?: number;
    account_id: string;
    account_name?: string;
    platform?: PlatformType;
    time_slot?: string;
    start?: string;
    end?: string;
  }>;
  upcoming_24h: Array<{
    post_id: string;
    target_id: string;
    title: string;
    platform: PlatformType;
    account_id: string;
    account_name: string;
    account_avatar?: string;
    status: string;
    scheduled_at?: string | null;
    thumb?: string;
    caption?: string;
  }>;
  overdue: Array<{
    post_id: string;
    target_id: string;
    title: string;
    platform: PlatformType;
    account_id: string;
    account_name: string;
    account_avatar?: string;
    status: string;
    scheduled_at?: string | null;
    thumb?: string;
    caption?: string;
  }>;
  failed: Array<{
    post_id: string;
    target_id: string;
    title: string;
    platform: PlatformType;
    account_id: string;
    account_name: string;
    account_avatar?: string;
    status: string;
    scheduled_at?: string | null;
    thumb?: string;
    caption?: string;
  }>;
  pending_approval: Array<{
    post_id: string;
    target_id: string;
    title: string;
    platform: PlatformType;
    account_id: string;
    account_name: string;
    account_avatar?: string;
    status: string;
    scheduled_at?: string | null;
    thumb?: string;
    caption?: string;
  }>;
  token_expiring_accounts: Array<{
    id: string;
    display_name: string;
    platform: PlatformType;
    expires_at: string;
    days_left: number;
  }>;
  empty_slots_7d: Array<{
    date: string;
    weekday: number;
    account_id: string;
    account_name: string;
    platform: PlatformType;
    start: string;
    end: string;
  }>;
}

export interface ContentTemplate {
  id: string;
  name: string;
  title?: string;
  purpose: "sales" | "koc" | "education" | "story" | "general";
  platforms: PlatformType[];
  caption_hook: string;
  caption_body: string;
  caption_cta: string;
  caption_template?: string;
  cta?: string;
  hashtags: string[];
  first_comment: string;
  footer: string;
  disclosure: string;
  created_at?: string;
  updated_at?: string;
}

export interface AccountStats {
  account_id: string;
  posts_this_week: number;
  posts_today: number;
  daily_limit: number;
  quota_remaining_today: number;
  next_post_time?: string | null;
  last_posted_at?: string | null;
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
  color: string;
}

export interface KPISummary {
  total_views: number;
  total_watch_time_s: number;
  avg_retention_pct: number;
  engagement_rate: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  total_saves: number;
  follower_gain: number;
  avg_ctr: number;
  affiliate_revenue: number;
  post_count: number;
}

export interface GoldenHourSlot {
  weekday: number;
  hour: number;
  median_views: number;
  sample_count: number;
  score: number;
}

export interface HeatmapData {
  matrix: GoldenHourSlot[][];
  top_slots: GoldenHourSlot[];
  recommended_windows: PostingWindow[];
}

export interface OutlierItem {
  post_id: string;
  target_id: string;
  title: string;
  platform: PlatformType;
  views: number;
  benchmark_views: number;
  ratio: number;
  kind: "top_outlier" | "underperforming";
  hypothesis: string;
}

export interface CreativePerformance {
  templates: {
    template_id: string;
    post_count: number;
    total_views: number;
    avg_views: number;
    avg_er: number;
  }[];
  blueprints: {
    blueprint_ref: string;
    post_count: number;
    total_views: number;
    avg_views: number;
    avg_er: number;
  }[];
}

export interface AutomationRule {
  id: string;
  name: string;
  enabled: boolean;
  trigger: "render_done" | "idea_scripted" | "schedule_gap";
  conditions: Record<string, any>;
  actions: Record<string, any>;
  last_run_at?: string | null;
  run_count: number;
  last_log?: string | null;
}

export interface SocialNotification {
  id: string;
  type: "publish_success" | "publish_failed" | "token_expired" | "manual_package_due" | "schedule_gap" | "system";
  title: string;
  message: string;
  created_at: string;
  read: boolean;
  action_url?: string | null;
  data?: Record<string, any>;
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
  views?: number;
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
  // Videos & Bulk Planning
  getVideos: (projectId: string) =>
    fetchJson<PublishableVideo[]>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/videos`),

  previewPlan: (projectId: string, payload: PlanPreviewRequest) =>
    fetchJson<PlannedTarget[]>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/plans/preview`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  commitPlan: (projectId: string, targets: TargetCommitSpec[], approvalRequired: boolean = true) =>
    fetchJson<{ created_posts_count: number; created_targets_count: number; posts: Post[] }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/plans/commit`,
      {
        method: "POST",
        body: JSON.stringify({ targets, approval_required: approvalRequired }),
      }
    ),

  generateCaptions: (projectId: string, payload: CaptionGenerateRequest) =>
    fetchJson<PlatformCaptionResult[]>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/captions/generate`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getQueue: (
    projectId: string,
    bucket: "draft" | "pending_approval" | "upcoming" | "overdue" | "published" | "failed" | "all" = "upcoming",
    params?: { accountId?: string; platform?: string; fromDate?: string }
  ) => {
    const q = new URLSearchParams();
    if (bucket && bucket !== "all") q.set("bucket", bucket);
    if (params?.accountId) q.set("account", params.accountId);
    if (params?.platform) q.set("platform", params.platform);
    if (params?.fromDate) q.set("from", params.fromDate);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return fetchJson<QueueResponse>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/queue${qs}`);
  },

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

  getPackageInfo: (projectId: string, postId: string, platform: string) =>
    fetchJson<{
      post_id: string;
      platform: string;
      package_dir: string;
      zip_path: string | null;
      zip_filename: string | null;
      has_real_video: boolean;
      caption: string;
      hashtags: string;
      checklist: string;
    }>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/packages/${postId}/${platform}`),

  generatePackage: (projectId: string, postId: string, platform: string) =>
    fetchJson<{
      post_id: string;
      platform: string;
      package_dir: string;
      zip_path: string;
      zip_filename: string;
      has_real_video: boolean;
      caption: string;
      hashtags: string;
      checklist: string;
    }>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/packages/${postId}/${platform}/generate`, {
      method: "POST",
    }),

  // Analytics & Insights
  getAnalyticsOverview: (
    projectId: string,
    window: string = "30d",
    platform?: string,
    accountId?: string
  ) => {
    const params = new URLSearchParams({ window });
    if (platform) params.append("platform", platform);
    if (accountId) params.append("account_id", accountId);
    return fetchJson<{
      kpis: KPISummary;
      views_by_day: Record<string, Record<string, number>>;
      outliers: { top_outliers: OutlierItem[]; underperforming: OutlierItem[] };
    }>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/analytics/overview?${params}`);
  },

  getAnalyticsHeatmap: (projectId: string) =>
    fetchJson<HeatmapData>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/analytics/heatmap`),

  applyGoldenWindows: (projectId: string, accountId?: string, windows?: PostingWindow[]) =>
    fetchJson<{ status: string; updated_accounts: string[]; windows: PostingWindow[] }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/analytics/apply-golden-windows`,
      {
        method: "POST",
        body: JSON.stringify({ account_id: accountId, windows }),
      }
    ),

  getCreativePerformance: (projectId: string) =>
    fetchJson<CreativePerformance>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/analytics/creatives`),

  getAnalyticsLearnings: (projectId: string) =>
    fetchJson<{ learnings_md: string; recommendations: any }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/analytics/learnings`
    ),

  generateInsights: (projectId: string) =>
    fetchJson<{
      status: string;
      date: string;
      kpis: KPISummary;
      learnings_md: string;
      recommendations: any;
    }>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/analytics/generate-insights`, {
      method: "POST",
    }),

  triggerAnalyticsCollect: (projectId: string) =>
    fetchJson<{ status: string; count: number }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/analytics/collect`,
      { method: "POST" }
    ),

  saveManualMetrics: (projectId: string, payload: any) =>
    fetchJson<{ status: string; snapshot: any }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/analytics/manual-metrics`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    ),

  importCsvMetrics: (projectId: string, csvText: string, platform?: string) =>
    fetchJson<{ status: string; total_records: number; matched_count: number; records: any[] }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/analytics/import-csv`,
      {
        method: "POST",
        body: JSON.stringify({ csv_text: csvText, platform: platform || "youtube" }),
      }
    ),

  // Automation Rules
  listAutomationRules: (projectId: string) =>
    fetchJson<AutomationRule[]>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/automation/rules`),

  saveAutomationRule: (projectId: string, rule: Partial<AutomationRule>) =>
    fetchJson<AutomationRule>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/automation/rules`, {
      method: "POST",
      body: JSON.stringify(rule),
    }),

  toggleAutomationRule: (projectId: string, ruleId: string) =>
    fetchJson<{ id: string; enabled: boolean }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/automation/rules/${ruleId}/toggle`,
      { method: "POST" }
    ),

  deleteAutomationRule: (projectId: string, ruleId: string) =>
    fetchJson<{ status: string; id: string }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/automation/rules/${ruleId}`,
      { method: "DELETE" }
    ),

  runAutomation: (projectId: string, ruleId?: string) => {
    const q = ruleId ? `?rule_id=${ruleId}` : "";
    return fetchJson<{ reports: any[] }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/automation/run${q}`,
      { method: "POST" }
    );
  },

  // Notifications
  listNotifications: (projectId: string, unreadOnly: boolean = false) =>
    fetchJson<SocialNotification[]>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/notifications?unread_only=${unreadOnly}`
    ),

  markNotificationRead: (projectId: string, notifId: string) =>
    fetchJson<{ status: string; success: boolean }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/notifications/${notifId}/read`,
      { method: "POST" }
    ),

  clearNotifications: (projectId: string) =>
    fetchJson<{ status: string }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/notifications`,
      { method: "DELETE" }
    ),

  // Hub APIs
  fetchLibrary: (
    projectId: string,
    params?: { filter?: string; account?: string; platform?: string; q?: string }
  ) => {
    const sp = new URLSearchParams();
    if (params?.filter) sp.append("filter", params.filter);
    if (params?.account) sp.append("account", params.account);
    if (params?.platform) sp.append("platform", params.platform);
    if (params?.q) sp.append("q", params.q);
    const qs = sp.toString() ? `?${sp.toString()}` : "";
    return fetchJson<LibraryVideo[]>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/library${qs}`
    );
  },

  fetchOverview: (projectId: string) =>
    fetchJson<SocialOverview>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/overview`),

  bulkAction: (
    projectId: string,
    payload: { ids: string[]; action: string; params?: any }
  ) =>
    fetchJson<{ results: Array<{ id: string; success: boolean; error?: string | null }> }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/targets/bulk`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    ),

  fetchTemplates: (projectId: string) =>
    fetchJson<ContentTemplate[]>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/templates`),

  createTemplate: (projectId: string, template: Partial<ContentTemplate>) =>
    fetchJson<ContentTemplate>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/templates`, {
      method: "POST",
      body: JSON.stringify(template),
    }),

  updateTemplate: (projectId: string, templateId: string, template: Partial<ContentTemplate>) =>
    fetchJson<ContentTemplate>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/templates/${templateId}`,
      {
        method: "PUT",
        body: JSON.stringify(template),
      }
    ),

  deleteTemplate: (projectId: string, templateId: string) =>
    fetchJson<{ status: string; template_id: string }>(
      `${SOCIAL_CORE_URL}/projects/${projectId}/social/templates/${templateId}`,
      { method: "DELETE" }
    ),

  fetchAccountStats: (projectId: string) =>
    fetchJson<AccountStats[]>(`${SOCIAL_CORE_URL}/projects/${projectId}/social/accounts/stats`),
};
