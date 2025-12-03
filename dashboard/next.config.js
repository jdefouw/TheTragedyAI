const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  webpack: (config, { dir }) => {
    // Use the dir parameter from Next.js which is the absolute path to the project
    const srcPath = path.resolve(dir, 'src')
    
    // Ensure resolve exists
    config.resolve = config.resolve || {}
    
    // Set up aliases - merge with existing to avoid conflicts
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      '@': srcPath,
    }
    
    // Ensure extensions include .ts and .tsx
    config.resolve.extensions = [
      ...(config.resolve.extensions || []),
      '.ts',
      '.tsx',
    ]
    
    return config
  },
}

module.exports = nextConfig