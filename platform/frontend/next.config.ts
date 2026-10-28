import type { NextConfig } from "next";
const config: NextConfig = {
  output: "standalone",
  skipTrailingSlashRedirect: true,
  async rewrites() {
    const origin = process.env.BACKEND_URL || "http://127.0.0.1:8000";
    return [
      { source: "/api/:path*", destination: `${origin}/api/:path*/` },
      { source: "/admin/:path*", destination: `${origin}/admin/:path*/` },
      { source: "/static/:path*", destination: `${origin}/static/:path*` },
    ];
  },
};
export default config;
