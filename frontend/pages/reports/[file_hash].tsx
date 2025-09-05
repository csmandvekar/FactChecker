import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import Layout from '@/components/Layout'

export default function ReportDetailPage() {
  const router = useRouter()
  const { file_hash } = router.query
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [evidencePreview, setEvidencePreview] = useState<Record<string, any>>({})
  const [previewLoading, setPreviewLoading] = useState<Record<string, boolean>>({})

  useEffect(() => {
    if (!file_hash) return
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/public/reports/${file_hash}`)
        if (!res.ok) {
          throw new Error(`Report not found`)
        }
        const json = await res.json()
        setData(json)
      } catch (e: any) {
        setError(e?.message || 'Failed to load report')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [file_hash])

  return (
    <Layout>
      <Head>
        <title>Report - DeepVerify Studio</title>
      </Head>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {loading && <p className="text-gray-600">Loading report…</p>}
        {error && <p className="text-red-600">{error}</p>}
        {!loading && !error && data && (
          <div className="space-y-6">
            <div className="card">
              <h1 className="text-2xl font-semibold text-gray-900 mb-2">{data.file_name || data.file_info?.filename || 'Report'}</h1>
              <p className="text-gray-600">Hash: {data.file_hash || data.file_info?.file_hash}</p>
              <p className="text-gray-600">Type: {data.file_type || data.file_info?.file_type}</p>
              {data.verdict && (
                <p className="text-gray-900 mt-2">Verdict: {data.verdict} ({data.confidence_score ? (data.confidence_score * 100).toFixed(1) + '%' : '—'})</p>
              )}
            </div>
            {data.analysis_result && (
              <div className="card">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Detailed Analyses</h2>
                <div className="space-y-3">
                  {Object.entries<any>(data.analysis_result).map(([k, v]) => (
                    <div key={k} className="bg-gray-50 rounded p-4">
                      <div className="font-medium text-gray-900 mb-1">{k}</div>
                      {v.result && <div className="text-gray-800">Result: {v.result}</div>}
                      {typeof v.confidence !== 'undefined' && <div className="text-gray-800">Confidence: {(v.confidence * 100).toFixed(1)}%</div>}
                      {v.evidence_link && (
                        <div className="mt-2">
                          {(() => {
                            const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
                            const raw = (v.evidence_link as string)
                            const normalized = raw.startsWith('http')
                              ? raw
                              : `${apiBase}/${raw
                                  .replace(/^[\\/]+/, '')
                                  .replace(/^static\\\\?/, 'static/')
                                  .replace(/^static\\/, 'static/')
                                  .replace(/\\/g, '/')}`
                            const isJson = normalized.toLowerCase().endsWith('.json')
                            return (
                              <div className="flex items-center space-x-4">
                                <a href={normalized} className="text-primary-600 hover:underline" target="_blank" rel="noreferrer">
                                  View evidence
                                </a>
                                {isJson && (
                                  <button
                                    className="text-sm text-primary-700 hover:underline"
                                    onClick={async () => {
                                      try {
                                        setPreviewLoading(prev => ({ ...prev, [k]: true }))
                                        const resp = await fetch(normalized)
                                        const json = await resp.json()
                                        setEvidencePreview(prev => ({ ...prev, [k]: json }))
                                      } catch (e) {
                                        setEvidencePreview(prev => ({ ...prev, [k]: { error: 'Failed to load evidence JSON' } }))
                                      } finally {
                                        setPreviewLoading(prev => ({ ...prev, [k]: false }))
                                      }
                                    }}
                                  >
                                    {previewLoading[k] ? 'Loading…' : 'Preview'}
                                  </button>
                                )}
                              </div>
                            )
                          })()}
                        </div>
                      )}
                      {evidencePreview[k] && (
                        <div className="mt-3 bg-white border border-gray-200 rounded p-3">
                          {evidencePreview[k].summary && (
                            <div className="mb-3">
                              <div className="font-medium text-gray-900">Summary</div>
                              <div className="text-sm text-gray-800 mb-2">
                                <span className="font-semibold">Risk score: {evidencePreview[k].summary.risk_score}/10</span>
                                <span className="ml-2 text-xs bg-gray-100 px-2 py-1 rounded">
                                  {evidencePreview[k].summary.risk_score <= 3 ? 'Low' : 
                                   evidencePreview[k].summary.risk_score <= 6 ? 'Medium' : 'High'} Risk
                                </span>
                              </div>
                              
                              {/* Risk Explanation */}
                              {evidencePreview[k].summary.risk_explanation && (
                                <div className="text-sm text-gray-700 bg-blue-50 p-3 rounded mb-3">
                                  <div className="font-medium text-blue-900 mb-1">Risk Assessment:</div>
                                  {evidencePreview[k].summary.risk_explanation}
                                </div>
                              )}
                              
                              {/* Security Flags */}
                              {Array.isArray(evidencePreview[k].summary.security_flags) && evidencePreview[k].summary.security_flags.length > 0 && (
                                <div className="mb-3">
                                  <div className="font-medium text-red-900 mb-1">🚨 Security Flags:</div>
                                  <ul className="list-disc list-inside text-sm text-red-800">
                                    {evidencePreview[k].summary.security_flags.map((flag: string, i: number) => (
                                      <li key={i}>{flag}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              
                              {/* Risk Indicators with Explanations */}
                              {Array.isArray(evidencePreview[k].summary.risk_indicators) && evidencePreview[k].summary.risk_indicators.length > 0 && (
                                <div>
                                  <div className="font-medium text-gray-900 mb-2">Detailed Risk Analysis:</div>
                                  <ul className="space-y-2">
                                    {evidencePreview[k].summary.risk_indicators.map((ri: string, i: number) => (
                                      <li key={i} className="text-sm text-gray-800 bg-gray-50 p-2 rounded">
                                        {ri}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* Display Charts */}
                          {evidencePreview[k].chart_paths && Object.keys(evidencePreview[k].chart_paths).length > 0 && (
                            <div className="mb-4">
                              <div className="font-medium text-gray-900 mb-2">Analysis Charts</div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {Object.entries(evidencePreview[k].chart_paths).map(([chartType, chartPath]: [string, string]) => {
                                  if (!chartPath) return null;
                                  
                                  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                                  const normalizedPath = chartPath.startsWith('http') 
                                    ? chartPath 
                                    : `${apiBase}/${chartPath.replace(/^[\\/]+/, '').replace(/\\/g, '/')}`;
                                  
                                  const chartLabels: Record<string, string> = {
                                    'object_distribution': 'Object Distribution',
                                    'risk_levels': 'Risk Levels',
                                    'metadata_timeline': 'Metadata Timeline',
                                    'structure_analysis': 'Structure Analysis'
                                  };
                                  
                                  return (
                                    <div key={chartType} className="text-center">
                                      <div className="text-sm text-gray-600 mb-2">{chartLabels[chartType] || chartType}</div>
                                      <img 
                                        src={normalizedPath} 
                                        alt={chartLabels[chartType] || chartType}
                                        className="w-full h-auto border border-gray-200 rounded"
                                        onError={(e) => {
                                          e.currentTarget.style.display = 'none';
                                        }}
                                      />
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}
                          
                          {evidencePreview[k].pikepdf_analysis?.metadata && (
                            <div className="mb-3">
                              <div className="font-medium text-gray-900">Metadata</div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-1">
                                {Object.entries(evidencePreview[k].pikepdf_analysis.metadata).map(([mk, mv]: any) => (
                                  <div key={mk} className="text-sm text-gray-800"><span className="text-gray-600">{mk}:</span> {String(mv)}</div>
                                ))}
                              </div>
                            </div>
                          )}
                          {Array.isArray(evidencePreview[k].pikepdf_analysis?.anomalies) && evidencePreview[k].pikepdf_analysis.anomalies.length > 0 && (
                            <div className="mb-3">
                              <div className="font-medium text-gray-900">Anomalies</div>
                              <div className="space-y-2">
                                {evidencePreview[k].pikepdf_analysis.anomalies.map((a: any, i: number) => (
                                  <div key={i} className="bg-yellow-50 border-l-4 border-yellow-400 p-3">
                                    <div className="flex items-start">
                                      <div className="flex-shrink-0">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                          a.severity === 'high' ? 'bg-red-100 text-red-800' :
                                          a.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                          'bg-green-100 text-green-800'
                                        }`}>
                                          {a.severity?.toUpperCase() || 'UNKNOWN'}
                                        </span>
                                      </div>
                                      <div className="ml-3 flex-1">
                                        <div className="text-sm font-medium text-yellow-900">
                                          {a.description}
                                        </div>
                                        {a.explanation && (
                                          <div className="mt-1 text-sm text-yellow-800">
                                            {a.explanation}
                                          </div>
                                        )}
                                        {a.technical_details && (
                                          <div className="mt-2 text-xs text-yellow-700 bg-yellow-100 p-2 rounded">
                                            <div className="font-medium">Technical Details:</div>
                                            {Object.entries(a.technical_details).map(([key, value]: [string, any]) => (
                                              <div key={key}><span className="font-medium">{key}:</span> {String(value)}</div>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* PDFiD Analysis Results */}
                          {evidencePreview[k].pdfid_analysis && !evidencePreview[k].pdfid_analysis.error && (
                            <div className="mb-3">
                              <div className="font-medium text-gray-900">PDFiD Analysis</div>
                              {evidencePreview[k].pdfid_analysis.objects && Object.keys(evidencePreview[k].pdfid_analysis.objects).length > 0 && (
                                <div className="mt-2">
                                  <div className="text-sm text-gray-600 mb-1">Object Counts:</div>
                                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                    {Object.entries(evidencePreview[k].pdfid_analysis.objects).map(([objType, count]: [string, number]) => (
                                      <div key={objType} className="text-sm text-gray-800">
                                        <span className="text-gray-600">{objType}:</span> {count}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                                                             {Array.isArray(evidencePreview[k].pdfid_analysis.suspicious_objects) && evidencePreview[k].pdfid_analysis.suspicious_objects.length > 0 && (
                                 <div className="mt-2">
                                   <div className="text-sm text-gray-600 mb-1">Suspicious Objects:</div>
                                   <div className="space-y-2">
                                     {evidencePreview[k].pdfid_analysis.suspicious_objects.map((obj: any, i: number) => (
                                       <div key={i} className="bg-red-50 border-l-4 border-red-400 p-2">
                                         <div className="flex items-start">
                                           <div className="flex-shrink-0">
                                             <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                               obj.risk_level === 'high' ? 'bg-red-100 text-red-800' :
                                               obj.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                               'bg-green-100 text-green-800'
                                             }`}>
                                               {obj.risk_level?.toUpperCase() || 'UNKNOWN'}
                                             </span>
                                           </div>
                                           <div className="ml-3 flex-1">
                                             <div className="text-sm font-medium text-red-900">
                                               {obj.type} (Count: {obj.count})
                                             </div>
                                             {obj.explanation && (
                                               <div className="mt-1 text-sm text-red-800">
                                                 {obj.explanation}
                                               </div>
                                             )}
                                           </div>
                                         </div>
                                       </div>
                                     ))}
                                   </div>
                                 </div>
                               )}
                            </div>
                          )}
                          
                          {/* Structure Analysis */}
                          {evidencePreview[k].pikepdf_analysis?.structure && (
                            <div className="mb-3">
                              <div className="font-medium text-gray-900">Document Structure</div>
                              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-1">
                                {Object.entries(evidencePreview[k].pikepdf_analysis.structure).map(([key, value]: [string, any]) => {
                                  if (key === 'suspicious_elements' || key === 'trailer_keys') return null;
                                                                     return (
                                     <div key={key} className="text-sm text-gray-800">
                                       <span className="text-gray-600">{key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:</span> {String(value)}
                                     </div>
                                   );
                                })}
                              </div>
                              {Array.isArray(evidencePreview[k].pikepdf_analysis.structure.suspicious_elements) && evidencePreview[k].pikepdf_analysis.structure.suspicious_elements.length > 0 && (
                                <div className="mt-2">
                                  <div className="text-sm text-gray-600 mb-1">Suspicious Elements:</div>
                                  <ul className="list-disc list-inside text-sm text-gray-800">
                                    {evidencePreview[k].pikepdf_analysis.structure.suspicious_elements.map((element: string, i: number) => (
                                      <li key={i}>{element}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  )
}


