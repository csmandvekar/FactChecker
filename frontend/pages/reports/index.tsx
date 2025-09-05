import { useEffect, useState } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import Layout from '@/components/Layout'

export default function ReportsListPage() {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        // Prefer local DB fallback by hitting our own API via Next fetch
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/public/reports`)
        if (!res.ok) throw new Error('Failed to load reports')
        const json = await res.json()
        const list = Array.isArray(json.reports) ? json.reports : json
        setItems(list || [])
      } catch (e: any) {
        setError(e?.message || 'Failed to load reports')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <Layout>
      <Head>
        <title>Reports - DeepVerify Studio</title>
      </Head>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">Recent Analyses</h1>
        {loading && <p className="text-gray-600">Loading…</p>}
        {error && <p className="text-red-600">{error}</p>}
        {!loading && !error && (
          <div className="space-y-3">
            {items.length === 0 && <p className="text-gray-600">No reports yet.</p>}
            {items.map((r: any) => (
              <div key={(r.id || r.file_hash || r.file_id)} className="card flex items-center justify-between">
                <div>
                  <div className="text-gray-900 font-medium">{r.file_name || r.filename || r.original_filename || 'Unknown file'}</div>
                  <div className="text-gray-600 text-sm">{r.file_type || 'file'}</div>
                </div>
                {r.file_hash && (
                  <Link href={`/reports/${r.file_hash}`} className="btn-primary">View</Link>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  )
}


