import type { NextConfig } from "next";

const API_BASE_URL = process.env.INTERNAL_API_URL || "http://backend:8000";

const nextConfig: NextConfig = {
  
  images: {
    unoptimized: true, // Docker 내부 사설 IP 차단을 우회하기 위한 안전장치
  },
  async rewrites() {
    return [
      {
        source: '/storage/:path*',
        destination: `${API_BASE_URL}/storage/:path*`,
      },
      {
        source: '/app/storage/:path*',
        destination: `${API_BASE_URL}/storage/:path*`,
      },
      {
        source: '/api/assets/:path*',
        destination: `${API_BASE_URL}/api/assets/:path*`,
      },
    ];
  },
};

export default nextConfig;
