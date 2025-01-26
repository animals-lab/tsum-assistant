/** @type {import('next').NextConfig} */
const nextConfig = {
  rewrites: async () => {
    const backendHost = process.env.BACKEND_HOST || 'localhost';
    const backendPort = process.env.BACKEND_PORT || '8000';
    const backendUrl = `http://${backendHost}:${backendPort}`;

    return [
      {
        source: "/api/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? `${backendUrl}/api/:path*`
            : "/api/",
      },
      {
        source: "/docs",
        destination:
          process.env.NODE_ENV === "development"
            ? `${backendUrl}/docs`
            : "/api/docs",
      },
      {
        source: "/openapi.json",
        destination:
          process.env.NODE_ENV === "development"
            ? `${backendUrl}/openapi.json`
            : "/api/openapi.json",
      },
    ];
  },
};

module.exports = nextConfig;
