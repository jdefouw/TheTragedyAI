const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  webpack: (config, { dir, isServer }) => {
    // Get absolute path to src directory
    const srcPath = path.resolve(dir, 'src')
    
    // Initialize resolve if it doesn't exist
    if (!config.resolve) {
      config.resolve = {}
    }
    
    // Initialize alias object
    if (!config.resolve.alias) {
      config.resolve.alias = {}
    }
    
    // Set the @ alias to point to src directory
    // This must be an absolute path
    config.resolve.alias['@'] = srcPath
    
    // Log for debugging (will show in build output)
    if (process.env.NODE_ENV === 'development') {
      console.log('Webpack alias @ configured to:', srcPath)
    }
    
    return config
  },
}

module.exports = nextConfig