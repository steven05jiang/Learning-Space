'use client'

import dynamic from 'next/dynamic'
import { Skeleton } from '@/components/ui/skeleton'

// Dynamically import with SSR disabled — react-force-graph-2d requires window/canvas
const KnowledgeGraph = dynamic(
  () => import('@/components/knowledge-graph').then((mod) => mod.KnowledgeGraph),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full w-full items-center justify-center">
        <div className="space-y-4 text-center">
          <Skeleton className="mx-auto h-64 w-64 rounded-full" />
          <p className="text-sm text-muted-foreground">Loading knowledge graph...</p>
        </div>
      </div>
    ),
  }
)

export default function KnowledgeGraphPage() {
  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col p-6">
      <div className="mb-4">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          Knowledge Graph
        </h2>
        <p className="text-muted-foreground">
          Explore relationships between topics and discover related resources
        </p>
      </div>
      <div className="flex-1 overflow-hidden rounded-xl border border-border bg-card">
        <KnowledgeGraph />
      </div>
    </div>
  )
}
