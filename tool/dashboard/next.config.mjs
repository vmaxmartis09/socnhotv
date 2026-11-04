import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["morphicons"],
  reactStrictMode: true,
  devIndicators: { position: "bottom-right" },
  images: {
    unoptimized: true,
  },
  // Bản Vercel không có Core: /core/* trả về ảnh chụp dữ liệu chỉ-đọc trong public/snapshot (tạo bằng scripts/build-snapshot.mjs).
  async rewrites() {
    if (process.env.SNAPSHOT_MODE !== "1") return [];
    return [
      { source: "/core/data/projects/:id/files/:path*", destination: "/snapshot/files/projects/:id/files/:path*" },
      { source: "/core/projects/:id/files/:path*", destination: "/snapshot/files/projects/:id/files/:path*" },
    ];
  },
};

export default withNextIntl(nextConfig);
