const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  webpack: (config, { dir, isServer }) => {
    // Get the absolute path to src directory relative to the config file
    const srcPath = path.join(dir, 'src')
    
    // Ensure resolve and alias exist
    if (!config.resolve) {
      config.resolve = {}
    }
    
    // Merge with existing aliases to avoid overwriting Next.js defaults
    const existingAliases = config.resolve.alias || {}
    config.resolve.alias = {
      ...existingAliases,
      '@': srcPath,
    }
    
    return config
  },
}

module.exports = nextConfig