/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  /* config options here */
  output: 'standalone', // Optimized for production docker builds
};

module.exports = nextConfig;
