import { useState } from 'react'
import Head from 'next/head'
import { motion } from 'framer-motion'
import { ShieldCheckIcon, DocumentMagnifyingGlassIcon, PhotoIcon, ChartBarIcon, ClipboardDocumentCheckIcon } from '@heroicons/react/24/outline'
import FileUpload from '@/components/FileUpload'
import Layout from '@/components/Layout'
import Link from 'next/link'

export default function Home() {
  const [uploadedFile, setUploadedFile] = useState<any>(null)

  return (
    <>
      <Head>
        <title>DeepVerify Studio - Forensic Analysis Platform</title>
        <meta name="description" content="Verify any corporate-media content with SOTA deepfake & document forensics" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Layout>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
          {/* Hero Section */}
          <section className="relative overflow-hidden">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="text-center"
              >
                <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
                  <span className="text-gradient">DeepVerify</span> Studio
                </h1>
                <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto">
                  Verify any corporate-media content in one click using SOTA deepfake & document forensics
                </p>
                <div className="flex justify-center space-x-4 mb-12">
                  <div className="flex items-center text-gray-600">
                    <ShieldCheckIcon className="h-6 w-6 mr-2 text-green-500" />
                    <span>PDF Forensics</span>
                  </div>
                  <div className="flex items-center text-gray-600">
                    <PhotoIcon className="h-6 w-6 mr-2 text-blue-500" />
                    <span>Image Analysis</span>
                  </div>
                  <div className="flex items-center text-gray-600">
                    <DocumentMagnifyingGlassIcon className="h-6 w-6 mr-2 text-purple-500" />
                    <span>Real-time Reports</span>
                  </div>
                </div>
                
                {/* Service Selection */}
                <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto mb-12">
                  <Link href="/forensics">
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="bg-white rounded-xl shadow-lg p-8 cursor-pointer border-2 border-transparent hover:border-blue-500 transition-all duration-300"
                    >
                      <div className="text-center">
                        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                          <ShieldCheckIcon className="h-8 w-8 text-blue-600" />
                        </div>
                        <h3 className="text-xl font-semibold text-gray-900 mb-2">Forensics Tool</h3>
                        <p className="text-gray-600 mb-4">
                          Upload PDFs and images for comprehensive forensic analysis
                        </p>
                        <div className="text-blue-600 font-medium">Start Analysis →</div>
                      </div>
                    </motion.div>
                  </Link>
                  
                  <Link href="/intelligence">
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="bg-white rounded-xl shadow-lg p-8 cursor-pointer border-2 border-transparent hover:border-green-500 transition-all duration-300"
                    >
                      <div className="text-center">
                        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                          <ChartBarIcon className="h-8 w-8 text-green-600" />
                        </div>
                        <h3 className="text-xl font-semibold text-gray-900 mb-2">Market Intelligence</h3>
                        <p className="text-gray-600 mb-4">
                          Analyze corporate announcements and fact-check content
                        </p>
                        <div className="text-green-600 font-medium">Explore Intelligence →</div>
                      </div>
                    </motion.div>
                  </Link>
                </div>
              </motion.div>
            </div>
          </section>

          {/* Upload Section */}
          <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              <FileUpload onFileUploaded={setUploadedFile} />
            </motion.div>
          </section>

          {/* Features Section */}
          <section className="bg-white py-24">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
                className="text-center mb-16"
              >
                <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                  Advanced Forensic Analysis
                </h2>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                  Our platform combines multiple forensic techniques to provide comprehensive analysis
                </p>
              </motion.div>

              <div className="grid md:grid-cols-3 gap-8">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.6 }}
                  className="card text-center"
                >
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <DocumentMagnifyingGlassIcon className="h-8 w-8 text-blue-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">PDF Forensics</h3>
                  <p className="text-gray-600">
                    Detect metadata tampering, embedded JavaScript, and suspicious objects using PDFiD and pikepdf
                  </p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.8 }}
                  className="card text-center"
                >
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <PhotoIcon className="h-8 w-8 text-green-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Image Analysis</h3>
                  <p className="text-gray-600">
                    Error Level Analysis (ELA) combined with CASIA CNN for tampering detection
                  </p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 1.0 }}
                  className="card text-center"
                >
                  <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <ShieldCheckIcon className="h-8 w-8 text-purple-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Provenance Tracking</h3>
                  <p className="text-gray-600">
                    SHA256 checksums and detailed audit trails for complete file integrity verification
                  </p>
                </motion.div>
              </div>
            </div>
          </section>

          {/* CTA Section */}
          <section className="bg-primary-600 py-16">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 1.2 }}
              >
                <h2 className="text-3xl font-bold text-white mb-4">
                  Ready to verify your content?
                </h2>
                <p className="text-xl text-primary-100 mb-8">
                  Upload your first file and get instant forensic analysis results
                </p>
                <button className="btn-secondary text-lg px-8 py-3">
                  Get Started Now
                </button>
              </motion.div>
            </div>
          </section>
        </div>
      </Layout>
    </>
  )
}
