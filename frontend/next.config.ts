import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    API_URL: process.env.API_URL || "http://35.171.2.221",
  },
};

export default nextConfig;
