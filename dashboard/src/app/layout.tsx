import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Tragedy of the Commons AI - Dashboard',
  description: 'Real-time monitoring and analysis dashboard for the Tragedy of the Commons AI simulation',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

