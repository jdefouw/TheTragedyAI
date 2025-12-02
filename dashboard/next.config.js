/** @type {import('next').NextConfig} */
const path = require('path')

const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  webpack: (config) => {
    // Always resolve @ to src relative to this config file's directory
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, 'src'),
    }
    
    // Add src to module resolution
    config.resolve.modules = [
      path.resolve(__dirname, 'src'),
      ...(config.resolve.modules || []),
    ]
    
    return config
  },
}

module.exports = nextConfig

