/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  // Em desenvolvimento, proxya /api para o Railway
  ...(process.env.NODE_ENV !== "production" && {
    async rewrites() {
      return [
        {
          source: "/api/:path*",
          destination: `${process.env.NEXT_PUBLIC_API_URL || "https://radiant-comfort-production-cd12.up.railway.app"}/:path*`,
        },
      ];
    },
  }),
};

module.exports = nextConfig;
