import { defineConfig, loadEnv, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

// Ánh xạ tên model hiển thị trong tool sang model của Gemini API (chưa kiểm tra với khóa thật).
const IMAGE_MODELS: Record<string, string> = {
  '🍌 Nano Banana Pro': 'gemini-3-pro-image-preview',
  '🍌 Nano Banana 2.1': 'gemini-2.5-flash-image',
  '🍌 Nano Banana 2 Lite': 'gemini-2.5-flash-image',
};
const VIDEO_MODELS: Record<string, string> = {
  'Omni 1.1 Flash': 'veo-3.1-fast-generate-preview', // Omni chỉ có trong Flow, dùng Veo thay thế
  'Veo 3.1 - Fast': 'veo-3.1-fast-generate-preview',
  'Veo 3.1 - Lite': 'veo-3.1-fast-generate-preview',
};
const API = 'https://generativelanguage.googleapis.com/v1beta';

const readBody = (req: any): Promise<any> =>
  new Promise((resolve, reject) => {
    let s = '';
    req.on('data', (c: Buffer) => (s += c));
    req.on('end', () => {
      try { resolve(JSON.parse(s || '{}')); } catch (e) { reject(e); }
    });
  });

function geminiApi(key: string): Plugin {
  const call = async (url: string, init: RequestInit = {}) => {
    const res = await fetch(url, { ...init, headers: { 'x-goog-api-key': key, 'Content-Type': 'application/json', ...(init.headers || {}) } });
    if (!res.ok) throw new Error(`Gemini API ${res.status}: ${(await res.text()).slice(0, 300)}`);
    return res;
  };
  return {
    name: 'gemini-api',
    configureServer(server) {
      server.middlewares.use('/api', async (req, res) => {
        const send = (code: number, data: unknown) => {
          res.statusCode = code;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify(data));
        };
        try {
          if (req.url === '/status') return send(200, { live: Boolean(key) });
          if (!key) return send(400, { error: 'Chưa có GEMINI_API_KEY' });
          const b = await readBody(req);
          if (req.url === '/image') {
            const model = IMAGE_MODELS[b.model] || 'gemini-2.5-flash-image';
            const parts: any[] = (b.references || []).map((r: any) => ({ inlineData: { mimeType: r.mimeType, data: r.base64 } }));
            parts.push({ text: b.prompt });
            const r = await (await call(`${API}/models/${model}:generateContent`, {
              method: 'POST',
              body: JSON.stringify({
                contents: [{ parts }],
                generationConfig: { responseModalities: ['IMAGE'], imageConfig: { aspectRatio: b.aspectRatio || '16:9' } },
              }),
            })).json();
            const img = r.candidates?.[0]?.content?.parts?.find((p: any) => p.inlineData);
            if (!img) throw new Error('API không trả về ảnh');
            return send(200, { base64: img.inlineData.data, mimeType: img.inlineData.mimeType || 'image/png' });
          }
          if (req.url === '/video') {
            const model = VIDEO_MODELS[b.model] || 'veo-3.1-fast-generate-preview';
            const instance: any = { prompt: b.prompt };
            if (b.firstFrame) instance.image = { bytesBase64Encoded: b.firstFrame.base64, mimeType: b.firstFrame.mimeType };
            let op = await (await call(`${API}/models/${model}:predictLongRunning`, {
              method: 'POST',
              body: JSON.stringify({ instances: [instance], parameters: { aspectRatio: b.aspectRatio || '16:9', durationSeconds: b.durationSeconds || 6 } }),
            })).json();
            for (let i = 0; i < 90 && !op.done; i++) {
              await new Promise((r) => setTimeout(r, 10000));
              op = await (await call(`${API}/${op.name}`)).json();
            }
            if (!op.done) throw new Error('Tạo video quá lâu, đã dừng chờ');
            if (op.error) throw new Error(op.error.message || 'Tạo video thất bại');
            const uri = op.response?.generateVideoResponse?.generatedSamples?.[0]?.video?.uri;
            if (!uri) throw new Error('API không trả về video');
            const buf = Buffer.from(await (await call(uri)).arrayBuffer());
            return send(200, { base64: buf.toString('base64'), mimeType: 'video/mp4' });
          }
          send(404, { error: 'Không có đường dẫn này' });
        } catch (e: any) {
          send(500, { error: e.message || String(e) });
        }
      });
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react(), geminiApi(env.GEMINI_API_KEY || '')],
    resolve: { alias: { 'flow-sdk': path.resolve(__dirname, 'src/flow-sdk.ts') } },
  };
});
