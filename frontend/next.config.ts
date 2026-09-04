import path from "node:path";
import type { NextConfig } from "next";

const API_ORIGIN = process.env.API_ORIGIN ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8010";

const nextConfig: NextConfig = {
  turbopack: {
    root: path.resolve(__dirname),
  },
  serverExternalPackages: ["@remotion/renderer", "@remotion/bundler", "@remotion/cli"],
  transpilePackages: ["remotion", "@remotion/player"],
  async rewrites() {
    return [
      { source: "/api/v1/:path*", destination: `${API_ORIGIN}/api/v1/:path*` },
      { source: "/audio/:path*", destination: `${API_ORIGIN}/audio/:path*` },
      { source: "/images/:path*", destination: `${API_ORIGIN}/images/:path*` },
    ];
  },
};

export default nextConfig;
