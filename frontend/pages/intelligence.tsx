import { useState, useEffect } from 'react'
import Head from 'next/head'
import { motion } from 'framer-motion'
import { 
  ChartBarIcon, 
  ClipboardDocumentCheckIcon, 
  DocumentTextIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline'
import Layout from '@/components/Layout'
import { 
  getAnnouncements, 
  getIntelligenceStats, 
  factCheckContent,
  getAnnouncementDetails 
} from '@/lib/api'

interface Announcement {
  id: number
  company_name: string
  company_symbol: string
  title: string
  announcement_date: string
  credibility_score: number | null
  status: string
  analysis_summary: any
}

interface Stats {
  total_announcements: number
  analyzed_announcements: number
  pending_announcements: number
  total_companies: number
  average_credibility_score: number
}

export default function IntelligencePage() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedTab, setSelectedTab] = useState<'announcements' | 'fact-checker'>('announcements')
  const [factCheckResult, setFactCheckResult] = useState<any>(null)
  const [factCheckLoading, setFactCheckLoading] = useState(false)
  const [textContent, setTextContent] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [announcementsData, statsData] = await Promise.all([
        getAnnouncements({ limit: 50 }),
        getIntelligenceStats()
      ])
      setAnnouncements(announcementsData.announcements)
      setStats(statsData)
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFactCheck = async () => {
    if (!textContent && !selectedFile) {
      alert('Please provide text content or upload a file')
      return
    }

    try {
      setFactCheckLoading(true)
      const result = await factCheckContent({
        text_content: textContent || undefined,
        file: selectedFile || undefined
      })
      setFactCheckResult(result)
    } catch (error) {
      console.error('Error fact-checking:', error)
      alert('Error performing fact-check. Please try again.')
    } finally {
      setFactCheckLoading(false)
    }
  }

  const getCredibilityColor = (score: number | null) => {
    if (score === null) return 'text-gray-500'
    if (score >= 8) return 'text-green-600'
    if (score >= 6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getCredibilityIcon = (score: number | null) => {
    if (score === null) return <ClockIcon className="h-5 w-5" />
    if (score >= 8) return <CheckCircleIcon className="h-5 w-5" />
    if (score >= 6) return <ExclamationTriangleIcon className="h-5 w-5" />
    return <XCircleIcon className="h-5 w-5" />
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'analyzed': return 'bg-green-100 text-green-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'analyzing': return 'bg-blue-100 text-blue-800'
      case 'failed': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <>
      <Head>
        <title>Market Intelligence - DeepVerify Studio</title>
        <meta name="description" content="Market Intelligence and Fact-Checker for corporate announcements" />
      </Head>

      <Layout>
        <div className="min-h-screen bg-gray-50">
          {/* Header */}
          <div className="bg-white shadow">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">Market Intelligence</h1>
                  <p className="text-gray-600 mt-2">Analyze corporate announcements and fact-check content</p>
                </div>
                <div className="flex items-center space-x-4">
                  <ChartBarIcon className="h-8 w-8 text-green-600" />
                </div>
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          {stats && (
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white rounded-lg shadow p-6"
                >
                  <div className="flex items-center">
                    <DocumentTextIcon className="h-8 w-8 text-blue-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Announcements</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.total_announcements}</p>
                    </div>
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="bg-white rounded-lg shadow p-6"
                >
                  <div className="flex items-center">
                    <CheckCircleIcon className="h-8 w-8 text-green-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Analyzed</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.analyzed_announcements}</p>
                    </div>
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="bg-white rounded-lg shadow p-6"
                >
                  <div className="flex items-center">
                    <ClockIcon className="h-8 w-8 text-yellow-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Pending</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.pending_announcements}</p>
                    </div>
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="bg-white rounded-lg shadow p-6"
                >
                  <div className="flex items-center">
                    <ChartBarIcon className="h-8 w-8 text-purple-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Avg. Credibility</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.average_credibility_score.toFixed(1)}</p>
                    </div>
                  </div>
                </motion.div>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8">
                <button
                  onClick={() => setSelectedTab('announcements')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    selectedTab === 'announcements'
                      ? 'border-green-500 text-green-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <DocumentTextIcon className="h-5 w-5 inline mr-2" />
                  Announcements
                </button>
                <button
                  onClick={() => setSelectedTab('fact-checker')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    selectedTab === 'fact-checker'
                      ? 'border-green-500 text-green-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <ClipboardDocumentCheckIcon className="h-5 w-5 inline mr-2" />
                  Fact-Checker
                </button>
              </nav>
            </div>
          </div>

          {/* Content */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {selectedTab === 'announcements' && (
              <div>
                {loading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
                    <p className="text-gray-600 mt-4">Loading announcements...</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {announcements.map((announcement, index) => (
                      <motion.div
                        key={announcement.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-2">
                              <h3 className="text-lg font-semibold text-gray-900">
                                {announcement.title}
                              </h3>
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(announcement.status)}`}>
                                {announcement.status}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">
                              {announcement.company_name} ({announcement.company_symbol})
                            </p>
                            <p className="text-sm text-gray-500">
                              {new Date(announcement.announcement_date).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="flex items-center space-x-4">
                            {announcement.credibility_score !== null && (
                              <div className="text-right">
                                <div className={`flex items-center space-x-1 ${getCredibilityColor(announcement.credibility_score)}`}>
                                  {getCredibilityIcon(announcement.credibility_score)}
                                  <span className="font-semibold">
                                    {announcement.credibility_score.toFixed(1)}/10
                                  </span>
                                </div>
                                <p className="text-xs text-gray-500">Credibility</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {selectedTab === 'fact-checker' && (
              <div className="max-w-4xl mx-auto">
                <div className="bg-white rounded-lg shadow p-8">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">Fact-Checker</h2>
                  
                  <div className="space-y-6">
                    {/* Text Input */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Paste Text Content
                      </label>
                      <textarea
                        value={textContent}
                        onChange={(e) => setTextContent(e.target.value)}
                        rows={6}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                        placeholder="Paste the content you want to fact-check here..."
                      />
                    </div>

                    {/* File Upload */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Or Upload File
                      </label>
                      <input
                        type="file"
                        accept=".pdf,.txt"
                        onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                      />
                    </div>

                    {/* Fact-Check Button */}
                    <button
                      onClick={handleFactCheck}
                      disabled={factCheckLoading || (!textContent && !selectedFile)}
                      className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                    >
                      {factCheckLoading ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                          <span>Fact-Checking...</span>
                        </>
                      ) : (
                        <>
                          <MagnifyingGlassIcon className="h-5 w-5" />
                          <span>Fact-Check Content</span>
                        </>
                      )}
                    </button>

                    {/* Results */}
                    {factCheckResult && (
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-8 p-6 bg-gray-50 rounded-lg"
                      >
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Fact-Check Results</h3>
                        
                        <div className="space-y-4">
                          <div className="flex items-center space-x-3">
                            <span className="font-medium">Status:</span>
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                              factCheckResult.verification_result === 'verified_authentic' 
                                ? 'bg-green-100 text-green-800'
                                : factCheckResult.verification_result === 'partially_verified'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {factCheckResult.verification_result.replace('_', ' ').toUpperCase()}
                            </span>
                          </div>
                          
                          <div className="flex items-center space-x-3">
                            <span className="font-medium">Confidence:</span>
                            <span className="text-lg font-semibold">
                              {(factCheckResult.confidence_score * 100).toFixed(1)}%
                            </span>
                          </div>

                          {factCheckResult.evidence && factCheckResult.evidence.length > 0 && (
                            <div>
                              <span className="font-medium">Evidence:</span>
                              <div className="mt-2 space-y-2">
                                {factCheckResult.evidence.map((evidence: any, index: number) => (
                                  <div key={index} className="p-3 bg-white rounded border">
                                    <p className="font-medium">{evidence.company_name}</p>
                                    <p className="text-sm text-gray-600">{evidence.title}</p>
                                    <p className="text-xs text-gray-500">
                                      {new Date(evidence.announcement_date).toLocaleDateString()}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {factCheckResult.recommendations && (
                            <div>
                              <span className="font-medium">Recommendations:</span>
                              <ul className="mt-2 space-y-1">
                                {factCheckResult.recommendations.map((rec: string, index: number) => (
                                  <li key={index} className="text-sm text-gray-700">• {rec}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </Layout>
    </>
  )
}
