import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion } from 'framer-motion'
import { CloudArrowUpIcon, DocumentIcon, PhotoIcon, XMarkIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { uploadFile } from '@/lib/api'

interface FileUploadProps {
  onFileUploaded: (file: any) => void
}

export default function FileUpload({ onFileUploaded }: FileUploadProps) {
  const [uploadedFile, setUploadedFile] = useState<any>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]
    
    // Validate file type
    const allowedTypes = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!allowedTypes.includes(fileExtension)) {
      toast.error('Invalid file type. Please upload a PDF or image file.')
      return
    }

    // Validate file size (100MB limit)
    if (file.size > 100 * 1024 * 1024) {
      toast.error('File size too large. Please upload a file smaller than 100MB.')
      return
    }

    setIsUploading(true)
    
    try {
      // Upload file
      const uploadResult = await uploadFile(file)
      const normalized = {
        ...uploadResult,
        file_type: (uploadResult as any).file_type || (uploadResult as any).metadata?.file_type,
        file_size: (uploadResult as any).file_size || (uploadResult as any).metadata?.file_size,
        filename: (uploadResult as any).filename || (uploadResult as any).metadata?.file_name,
      }
      setUploadedFile(normalized)
      onFileUploaded(normalized)
      
      toast.success('File uploaded successfully!')
      
      // Background analysis is started automatically; optionally poll for status here
      setIsAnalyzing(true)
      // Simple poll for up to ~10s
      const start = Date.now()
      let finalData: any = null
      while (Date.now() - start < 10000) {
        try {
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/public/reports/${uploadResult.file_hash}`)
          if (res.ok) {
            finalData = await res.json()
            break
          }
        } catch (e) {}
        await new Promise(r => setTimeout(r, 1000))
      }
      setUploadedFile(prev => ({ ...prev, analysis: finalData }))
      toast.success(finalData ? 'Analysis completed!' : 'Analysis started. Results will be ready soon.')
      
    } catch (error) {
      console.error('Upload error:', error)
      toast.error('Failed to upload file. Please try again.')
    } finally {
      setIsUploading(false)
      setIsAnalyzing(false)
    }
  }, [onFileUploaded])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
    },
    multiple: false
  })

  const removeFile = () => {
    setUploadedFile(null)
    onFileUploaded(null)
  }

  const getFileIcon = (fileType: string) => {
    if (fileType === 'pdf') {
      return <DocumentIcon className="h-12 w-12 text-red-500" />
    } else {
      return <PhotoIcon className="h-12 w-12 text-blue-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'authentic':
        return 'text-green-600 bg-green-100'
      case 'suspicious':
        return 'text-yellow-600 bg-yellow-100'
      case 'malicious':
        return 'text-red-600 bg-red-100'
      case 'processing':
        return 'text-blue-600 bg-blue-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      {!uploadedFile && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card"
        >
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-primary-400 bg-primary-50'
                : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
            }`}
          >
            <input {...getInputProps()} />
            
            <CloudArrowUpIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            
            {isDragActive ? (
              <p className="text-lg text-primary-600 font-medium">
                Drop your file here...
              </p>
            ) : (
              <div>
                <p className="text-lg text-gray-900 font-medium mb-2">
                  Upload a file for analysis
                </p>
                <p className="text-gray-600 mb-4">
                  Drag and drop your PDF or image file here, or click to browse
                </p>
                <p className="text-sm text-gray-500">
                  Supported formats: PDF, JPG, PNG, GIF, BMP, TIFF (Max 100MB)
                </p>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Upload Progress */}
      {isUploading && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          <div className="flex items-center space-x-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <div>
              <p className="text-lg font-medium text-gray-900">Uploading file...</p>
              <p className="text-gray-600">Please wait while we process your file</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Analysis Progress */}
      {isAnalyzing && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          <div className="flex items-center space-x-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <div>
              <p className="text-lg font-medium text-gray-900">Analyzing file...</p>
              <p className="text-gray-600">Running forensic analysis</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Uploaded File Info */}
      {uploadedFile && !isUploading && !isAnalyzing && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              {getFileIcon(uploadedFile.file_type)}
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  {uploadedFile?.filename || 'Uploaded file'}
                </h3>
                <p className="text-gray-600">
                  {(uploadedFile?.file_type || '').toString().toUpperCase() || 'FILE'} • {uploadedFile?.file_size ? (uploadedFile.file_size / 1024 / 1024).toFixed(2) : '—'} MB
                </p>
                {uploadedFile.analysis && (
                  <div className="mt-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(uploadedFile.analysis.verdict)}`}>
                      {uploadedFile.analysis.verdict}
                    </span>
                    <span className="ml-2 text-sm text-gray-600">
                      Confidence: {(uploadedFile.analysis.confidence_score * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
            
            <button
              onClick={removeFile}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          
          {uploadedFile.analysis && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Analysis Results</h4>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h5 className="font-medium text-gray-900 mb-2">Verdict</h5>
                  <p className="text-gray-600">{uploadedFile.analysis.verdict}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h5 className="font-medium text-gray-900 mb-2">Confidence</h5>
                  <p className="text-gray-600">{(uploadedFile.analysis.confidence_score * 100).toFixed(1)}%</p>
                </div>
              </div>
              
              <div className="mt-4">
                <a
                  href={`/reports/${uploadedFile.file_hash}`}
                  className="btn-primary"
                >
                  View Detailed Report
                </a>
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
