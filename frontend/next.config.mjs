/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // matches the production Docker stage (.next/standalone)
  env: {
    // Surface the deploy git SHA (Vercel sets VERCEL_GIT_COMMIT_SHA) to the client as a 7-char build id.
    NEXT_PUBLIC_COMMIT_SHA: (process.env.VERCEL_GIT_COMMIT_SHA ?? '').slice(0, 7),
  },
};

export default nextConfig;
