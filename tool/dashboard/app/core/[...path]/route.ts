// Bản Vercel không có Core: trả ảnh chụp dữ liệu chỉ-đọc từ /snapshot (tạo bằng scripts/build-snapshot.mjs).
// Các lời gọi ghi (POST...) nhận 405 để giao diện tự chuyển sang chế độ chạy thử.
export const dynamic = "force-dynamic";

export async function GET(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  const url = new URL(`/snapshot/${path.join("/")}.json`, req.url);
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) return Response.json({ detail: "Không có trong ảnh chụp" }, { status: 404 });
  return new Response(r.body, { headers: { "content-type": "application/json", "cache-control": "public, max-age=60" } });
}

const readOnly = () => Response.json({ detail: "Bản xem trên Vercel là chỉ-đọc; chạy Core cục bộ để chỉnh sửa." }, { status: 405 });
export const POST = readOnly, PUT = readOnly, PATCH = readOnly, DELETE = readOnly;
