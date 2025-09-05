import { useState } from 'react'
import Head from 'next/head'
import { motion } from 'framer-motion'
import { ShieldCheckIcon, DocumentMagnifyingGlassIcon, PhotoIcon } from '@heroicons/react/24/outline'
import FileUpload from '@/components/FileUpload'
import Layout from '@/components/Layout'

export default function ForensicsPage() {
  const [uploadedFile, setUploadedFile] = useState<any>(null)

  return (
    <>
      <Head>
        <title>Forensics Tool - DeepVerify Studio</title>
        <meta name="description" content="Upload PDFs and images for comprehensive forensic analysis" />
      </Head>

      <Layout>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
          {/* Header */}
          <div className="bg-white shadow">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">Forensics Tool</h1>
                  <p className="text-gray-600 mt-2">Upload PDFs and images for comprehensive forensic analysis</p>
                </div>
                <div className="flex items-center space-x-4">
                  <ShieldCheckIcon className="h-8 w-8 text-blue-600" />
                </div>
              </div>
            </div>
          </div>

          {/* Upload Section */}
          <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <FileUpload onFileUploaded={setUploadedFile} />
            </motion.div>
          </section>

          {/* Features Section */}
          <section className="bg-white py-16">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
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
                  transition={{ duration: 0.8, delay: 0.4 }}
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
                  transition={{ duration: 0.8, delay: 0.6 }}
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
                  transition={{ duration: 0.8, delay: 0.8 }}
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
        </div>
      </Layout>
    </>
  )
}
