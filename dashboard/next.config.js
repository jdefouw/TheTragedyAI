/** @type {import('next').NextConfig} */
const path = require('path')

const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  webpack: (config, { defaultLoaders }) => {
    // Resolve @ alias to src directory
    const srcPath = path.resolve(__dirname, 'src')
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': srcPath,
    }
    
    // Ensure modules are resolved from the dashboard directory
    config.resolve.modules = [
      path.resolve(__dirname, 'node_modules'),
      'node_modules',
    ]
    
    return config
  },
}

module.exports = nextConfig

