import { ReactNode, useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { ShieldCheckIcon } from '@heroicons/react/24/outline'
import api, { getCurrentUser, logout } from '@/lib/api'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
    if (!token) {
      setUser(null)
      return
    }
    getCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
  }, [])
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <ShieldCheckIcon className="h-8 w-8 text-primary-600 mr-3" />
              <span className="text-xl font-bold text-gray-900">DeepVerify Studio</span>
            </div>
            
            <nav className="hidden md:flex space-x-8">
              <a href="/" className="text-gray-600 hover:text-gray-900 transition-colors">
                Home
              </a>
              <a href="/reports" className="text-gray-600 hover:text-gray-900 transition-colors">
                Reports
              </a>
              <a href="/about" className="text-gray-600 hover:text-gray-900 transition-colors">
                About
              </a>
            </nav>
            
            <div className="flex items-center space-x-4">
              {user ? (
                <>
                  <span className="text-gray-700">{user.username || user.email}</span>
                  <button
                    className="btn-secondary"
                    onClick={async () => {
                      await logout()
                      window.location.href = '/'
                    }}
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link href="/login" className="btn-primary">Sign In</Link>
                  <Link href="/signup" className="btn-secondary">Sign Up</Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="col-span-2">
              <div className="flex items-center mb-4">
                <ShieldCheckIcon className="h-8 w-8 text-primary-400 mr-3" />
                <span className="text-xl font-bold">DeepVerify Studio</span>
              </div>
              <p className="text-gray-400 mb-4 max-w-md">
                Advanced forensic analysis platform for detecting deepfakes and document tampering.
                Verify any corporate-media content with confidence.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-4">Features</h3>
              <ul className="space-y-2 text-gray-400">
                <li>PDF Forensics</li>
                <li>Image Analysis</li>
                <li>Real-time Reports</li>
                <li>Provenance Tracking</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-gray-400">
                <li>Documentation</li>
                <li>API Reference</li>
                <li>Contact Us</li>
                <li>Privacy Policy</li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 DeepVerify Studio. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
