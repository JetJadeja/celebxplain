import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  images: {
    domains: [
      "localhost",
      "picsum.photos",
      "edm.com",
      "cloudfront-us-east-1.images.arcpublishing.com",
      "i.ytimg.com",
      "mediaproxy.salon.com",
      "media.cnn.com",
      "images.cdn.prd.api.discomax.com",
    ],
  },
};

export default nextConfig;
