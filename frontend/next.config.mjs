/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // matches the production Docker stage (.next/standalone)
};

export default nextConfig;
