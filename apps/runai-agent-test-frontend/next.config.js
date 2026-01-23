// Try to load next-runtime-env, but make it optional for build-time
let configureRuntimeEnv;
try {
  configureRuntimeEnv = require('next-runtime-env/build/configure').configureRuntimeEnv;
} catch (e) {
  // Fallback if next-runtime-env is not available
  configureRuntimeEnv = () => ({});
}

// Next.js is built WITH basePath at container startup
// The basePath is determined from RUNAI_PROJECT and RUNAI_JOB_NAME environment variables
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

const nextConfig = {
  basePath: basePath,
  assetPrefix: basePath,
  env: {
    ...configureRuntimeEnv(),
  },
  output: 'standalone',
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    // !! WARN !!
    ignoreBuildErrors: true,
  },
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  experimental: {
    serverActions: {
      bodySizeLimit: '5mb',
    },
  },
  webpack(config, { isServer, dev }) {
    config.experiments = {
      asyncWebAssembly: true,
      layers: true,
    };

    return config;
  },
  async redirects() {
    return [];
  },
};

module.exports = nextConfig;
