import type { NextConfig } from "next";

const siteV3AssetPrefix = process.env.SITE_V3_ASSET_PREFIX?.replace(/\/+$/, "");

const nextConfig: NextConfig = {
  assetPrefix: siteV3AssetPrefix || undefined,
  async rewrites() {
    if (!siteV3AssetPrefix) {
      return [];
    }
    return [
      {
        source: `${siteV3AssetPrefix}/:path*`,
        destination: "/:path*",
      },
    ];
  },
};

export default nextConfig;
