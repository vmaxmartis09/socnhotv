// Bản thay thế "flow-sdk" để chạy tool ngoài Google Flow.
// Có khóa GEMINI_API_KEY ở server -> gọi API thật; không có -> chế độ chạy thử (ảnh/video giả, không tốn tiền).

type Media = { mediaId: string; base64: string; mimeType: string };

const store = new Map<string, { base64: string; mimeType: string }>();
let counter = 0;

const remember = (base64: string, mimeType: string): Media => {
  const mediaId = `local-${Date.now()}-${++counter}`;
  store.set(mediaId, { base64, mimeType });
  return { mediaId, base64, mimeType };
};

let liveCache: boolean | null = null;
const isLive = async (): Promise<boolean> => {
  if (liveCache !== null) return liveCache;
  try {
    liveCache = Boolean((await (await fetch('/api/status')).json()).live);
  } catch {
    liveCache = false;
  }
  return liveCache;
};

const post = async (url: string, body: unknown) => {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Lỗi máy chủ ${res.status}`);
  return data as { base64: string; mimeType: string };
};

const toBase64 = (blob: Blob): Promise<string> =>
  new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(',')[1] || '');
    r.onerror = () => reject(r.error);
    r.readAsDataURL(blob);
  });

const canvasFor = (aspectRatio: string) => {
  const c = document.createElement('canvas');
  c.width = aspectRatio === '1:1' ? 768 : 1280;
  c.height = aspectRatio === '1:1' ? 768 : 720;
  return c;
};

const drawMock = (c: HTMLCanvasElement, label: string, t = 0) => {
  const g = c.getContext('2d')!;
  const grad = g.createLinearGradient(0, 0, c.width, c.height);
  grad.addColorStop(0, '#fde68a');
  grad.addColorStop(1, '#f59e0b');
  g.fillStyle = grad;
  g.fillRect(0, 0, c.width, c.height);
  g.fillStyle = 'rgba(0,0,0,0.55)';
  g.beginPath();
  g.arc(c.width / 2 + Math.sin(t) * 120, c.height / 2, 90, 0, Math.PI * 2);
  g.fill();
  g.fillStyle = '#1f2937';
  g.font = 'bold 30px sans-serif';
  g.textAlign = 'center';
  g.fillText('CHẠY THỬ (ảnh giả)', c.width / 2, 70);
  g.font = '22px sans-serif';
  g.fillText(label.slice(0, 70), c.width / 2, c.height - 50);
};

const mockImage = async (prompt: string, aspectRatio: string): Promise<{ base64: string; mimeType: string }> => {
  const c = canvasFor(aspectRatio);
  drawMock(c, prompt);
  await new Promise((r) => setTimeout(r, 600));
  return { base64: c.toDataURL('image/png').split(',')[1], mimeType: 'image/png' };
};

const mockVideo = async (prompt: string, seconds: number): Promise<{ base64: string; mimeType: string }> => {
  const c = canvasFor('16:9');
  const stream = c.captureStream(24);
  const rec = new MediaRecorder(stream, { mimeType: 'video/webm' });
  const chunks: Blob[] = [];
  rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  const done = new Promise<void>((r) => (rec.onstop = () => r()));
  rec.start();
  const start = performance.now();
  const total = Math.min(seconds, 2) * 1000;
  await new Promise<void>((resolve) => {
    const tick = () => {
      const el = performance.now() - start;
      drawMock(c, prompt, el / 400);
      el < total ? requestAnimationFrame(tick) : resolve();
    };
    tick();
  });
  rec.stop();
  await done;
  return { base64: await toBase64(new Blob(chunks, { type: 'video/webm' })), mimeType: 'video/webm' };
};

const refs = (ids?: string[]) =>
  (ids || []).map((id) => store.get(id)).filter(Boolean) as { base64: string; mimeType: string }[];

export const Flow = {
  generate: {
    async image(opts: {
      prompt: string;
      modelDisplayName?: string;
      aspectRatio?: string;
      referenceImageMediaIds?: string[];
    }): Promise<Media> {
      const aspectRatio = opts.aspectRatio || '16:9';
      const out = (await isLive())
        ? await post('/api/image', {
            prompt: opts.prompt,
            model: opts.modelDisplayName,
            aspectRatio,
            references: refs(opts.referenceImageMediaIds),
          })
        : await mockImage(opts.prompt, aspectRatio);
      return remember(out.base64, out.mimeType);
    },
    async video(opts: {
      prompt: string;
      modelDisplayName?: string;
      aspectRatio?: string;
      durationSeconds?: number;
      firstFrameImageMediaId?: string;
    }): Promise<Media> {
      const seconds = opts.durationSeconds || 6;
      const first = opts.firstFrameImageMediaId ? store.get(opts.firstFrameImageMediaId) : undefined;
      const out = (await isLive())
        ? await post('/api/video', {
            prompt: opts.prompt,
            model: opts.modelDisplayName,
            aspectRatio: opts.aspectRatio || '16:9',
            durationSeconds: seconds,
            firstFrame: first,
          })
        : await mockVideo(opts.prompt, seconds);
      return remember(out.base64, out.mimeType);
    },
  },

  async upload(opts: { base64: string; mimeType?: string; name?: string }): Promise<{ mediaId: string }> {
    const { mediaId } = remember(opts.base64, opts.mimeType || 'image/png');
    return { mediaId };
  },

  media: {
    select(opts?: { filter?: string }): Promise<Media> {
      return new Promise((resolve, reject) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = opts?.filter === 'video' ? 'video/*' : 'image/*';
        input.onchange = async () => {
          const file = input.files?.[0];
          if (!file) return reject(new Error('Đã hủy chọn tệp'));
          resolve(remember(await toBase64(file), file.type || 'image/png'));
        };
        input.oncancel = () => reject(new Error('Đã hủy chọn tệp'));
        input.click();
      });
    },
  },

  async download(opts: { base64: string; mimeType: string; filename: string }): Promise<void> {
    const bytes = Uint8Array.from(atob(opts.base64), (ch) => ch.charCodeAt(0));
    const url = URL.createObjectURL(new Blob([bytes], { type: opts.mimeType }));
    const a = document.createElement('a');
    a.href = url;
    a.download = opts.filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  },
};
