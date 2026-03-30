"use client";

import { useCallback, useRef, useState, useEffect, useMemo } from "react";
import Link from "next/link";
import ForceGraph2D, {
  type ForceGraphMethods,
  type NodeObject,
  type LinkObject,
} from "react-force-graph-2d";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  Link2,
} from "lucide-react";

// API response types
interface ApiGraphNode {
  id: string;
  label: string;
  level: string; // "root", "current", "child", "parent"
  node_type?: string; // "root", "category", "topic"
}
interface ApiGraphEdge {
  source: string;
  target: string;
  weight: number;
}
interface ApiGraphResponse {
  nodes: ApiGraphNode[];
  edges: ApiGraphEdge[];
}
interface ApiResource {
  id: string;
  title: string;
  summary: string | null;
  status: string;
  tags: string[];
  url?: string;
}
interface ApiNodeResourcesResponse {
  items: ApiResource[];
  total: number;
}

interface KnowledgeNode extends NodeObject {
  id: string;
  name: string;
  category: string;
  color: string;
  val?: number;
  node_type?: string;
}

interface KnowledgeLink extends LinkObject {
  source: string;
  target: string;
  relationship: string;
}

// Helper functions
function mapApiToGraphData(data: ApiGraphResponse): { nodes: KnowledgeNode[]; links: KnowledgeLink[] } {
  const colorByLevel: Record<string, string> = {
    root: '#60a5fa',
    current: '#60a5fa',
    child: '#34d399',
    parent: '#a78bfa',
  };
  const valByType: Record<string, number> = {
    root: 30,
    category: 20,
    topic: 8,
  };
  const nodes: KnowledgeNode[] = data.nodes.map((n) => ({
    id: n.id,
    name: n.label,
    category: n.level,
    node_type: n.node_type,
    color: n.node_type === 'root' ? '#f59e0b' : (colorByLevel[n.level] ?? '#818cf8'),
    val: valByType[n.node_type ?? ''] ?? 10,
  }));
  const links: KnowledgeLink[] = data.edges.map((e) => ({
    source: e.source,
    target: e.target,
    relationship: String(e.weight),
  }));
  return { nodes, links };
}

function mergeGraphData(
  existing: { nodes: KnowledgeNode[]; links: KnowledgeLink[] },
  newData: ApiGraphResponse
): { nodes: KnowledgeNode[]; links: KnowledgeLink[] } {
  const existingIds = new Set(existing.nodes.map((n) => n.id));
  const colorByLevel: Record<string, string> = { root: '#60a5fa', current: '#60a5fa', child: '#34d399', parent: '#a78bfa' };
  const valByType: Record<string, number> = { root: 30, category: 20, topic: 8 };
  const newNodes = newData.nodes
    .filter((n) => !existingIds.has(n.id))
    .map((n) => ({
      id: n.id,
      name: n.label,
      category: n.level,
      node_type: n.node_type,
      color: n.node_type === 'root' ? '#f59e0b' : (colorByLevel[n.level] ?? '#818cf8'),
      val: valByType[n.node_type ?? ''] ?? 10,
    }));
  const existingEdgeKeys = new Set(existing.links.map((l) => `${l.source}-${l.target}`));
  const newLinks = newData.edges
    .filter((e) => !existingEdgeKeys.has(`${e.source}-${e.target}`) && !existingEdgeKeys.has(`${e.target}-${e.source}`))
    .map((e) => ({ source: e.source, target: e.target, relationship: String(e.weight) }));
  return { nodes: [...existing.nodes, ...newNodes], links: [...existing.links, ...newLinks] };
}

export function KnowledgeGraph() {
  const graphRef = useRef<ForceGraphMethods>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null);
  const [adjacentNodes, setAdjacentNodes] = useState<KnowledgeNode[]>([]);
  const [adjacentLinks, setAdjacentLinks] = useState<KnowledgeLink[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());
  const [highlightLinks, setHighlightLinks] = useState<Set<string>>(new Set());
  const [graphData, setGraphData] = useState<{ nodes: KnowledgeNode[]; links: KnowledgeLink[] }>({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [nodeResources, setNodeResources] = useState<ApiResource[]>([]);
  const [resourcesLoading, setResourcesLoading] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const hasCenteredRef = useRef(false);
  // Stable ref to graphData so dimension-change effect always reads current node positions
  const graphDataRef = useRef(graphData);
  useEffect(() => { graphDataRef.current = graphData; }, [graphData]);

  // Derive category nodes from graph data
  const categoryNodes = useMemo(
    () => graphData.nodes.filter((n) => n.node_type === 'category'),
    [graphData.nodes],
  );

  const CATEGORY_PALETTE = ['#60a5fa', '#fbbf24', '#818cf8', '#f87171', '#34d399', '#fb923c', '#a78bfa', '#4ade80'];

  // Compute filtered node IDs when categories are selected
  const filteredNodeIds = useMemo(() => {
    if (selectedCategories.size === 0) return null;
    const visible = new Set<string>(selectedCategories);
    graphData.links.forEach((link) => {
      const srcId = typeof link.source === 'object' ? (link.source as KnowledgeNode).id : link.source as string;
      const tgtId = typeof link.target === 'object' ? (link.target as KnowledgeNode).id : link.target as string;
      if (selectedCategories.has(srcId)) visible.add(tgtId);
      if (selectedCategories.has(tgtId)) visible.add(srcId);
    });
    return visible;
  }, [selectedCategories, graphData]);

  // Configure d3 forces for better node spacing
  useEffect(() => {
    if (!graphRef.current) return;
    graphRef.current.d3Force('charge')?.strength(-250);
    graphRef.current.d3Force('link')?.distance(80);
  }, [graphData]);

  // After a dimension change ForceGraph2D may shift its viewport. Re-pin to root instantly.
  useEffect(() => {
    if (!hasCenteredRef.current) return;
    const rootNode = graphDataRef.current.nodes.find((n) => n.node_type === "root");
    if (rootNode?.x != null && rootNode?.y != null) {
      graphRef.current?.centerAt(rootNode.x, rootNode.y, 0);
    }
  }, [dimensions]);

  // Handle container resize
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Load graph data on mount
  useEffect(() => {
    async function loadGraph() {
      try {
        setIsLoading(true);
        const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
        const token = localStorage.getItem("auth_token");
        const res = await fetch(`${apiBase}/graph`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!res.ok) throw new Error('Failed to load graph');
        const data: ApiGraphResponse = await res.json();
        setGraphData(mapApiToGraphData(data));
      } catch (e) {
        setLoadError('Could not load knowledge graph.');
      } finally {
        setIsLoading(false);
      }
    }
    loadGraph();
  }, []);

  const handleReindex = useCallback(async () => {
    setIsReindexing(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      const token = localStorage.getItem("auth_token");
      const res = await fetch(`${apiBase}/graph/reindex`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("Reindex failed");
      // Reload the graph after cleanup
      const graphRes = await fetch(`${apiBase}/graph`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (graphRes.ok) {
        const data: ApiGraphResponse = await graphRes.json();
        hasCenteredRef.current = false;
        setGraphData(mapApiToGraphData(data));
      }
    } catch {
      // non-blocking — graph stays as-is if reindex fails
    } finally {
      setIsReindexing(false);
    }
  }, []);

  const handleNodeClick = useCallback(async (node: NodeObject) => {
    const knowledgeNode = node as KnowledgeNode;
    setSelectedNode(knowledgeNode);
    setIsDialogOpen(true);
    setResourcesLoading(true);

    // Find adjacent nodes and links using current graph state
    const adjLinks = graphData.links.filter(
      (link) =>
        link.source === knowledgeNode.id || link.target === knowledgeNode.id,
    );
    setAdjacentLinks(adjLinks);

    const adjNodeIds = new Set<string>();
    adjLinks.forEach((link) => {
      if (link.source === knowledgeNode.id) adjNodeIds.add(link.target);
      if (link.target === knowledgeNode.id) adjNodeIds.add(link.source);
    });

    const adjNodes = graphData.nodes.filter((n) => adjNodeIds.has(n.id));
    setAdjacentNodes(adjNodes);

    // Set highlights
    const newHighlightNodes = new Set<string>([
      knowledgeNode.id,
      ...adjNodeIds,
    ]);
    const newHighlightLinks = new Set<string>(
      adjLinks.map((l) => `${l.source}-${l.target}`),
    );
    setHighlightNodes(newHighlightNodes);
    setHighlightLinks(newHighlightLinks);

    // Fetch real resources for this node
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      const token = localStorage.getItem("auth_token");
      const authHeader = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${apiBase}/graph/nodes/${encodeURIComponent(knowledgeNode.id)}/resources`, {
        headers: authHeader,
      });
      if (res.ok) {
        const data: ApiNodeResourcesResponse = await res.json();
        setNodeResources(data.items);
      } else {
        setNodeResources([]);
      }
    } catch {
      setNodeResources([]);
    } finally {
      setResourcesLoading(false);
    }

    // Also call POST /api/graph/expand to get neighbors (merge into graph)
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      const token = localStorage.getItem("auth_token");
      const authHeader = token ? { Authorization: `Bearer ${token}` } : {};
      const expandRes = await fetch(`${apiBase}/graph/expand`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader },
        body: JSON.stringify({ node_id: knowledgeNode.id }),
      });
      if (expandRes.ok) {
        const expandData: ApiGraphResponse = await expandRes.json();
        setGraphData(prev => mergeGraphData(prev, expandData));
      }
    } catch {
      // non-blocking
    }

    // Zoom to the node
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 500);
      graphRef.current.zoom(2, 500);
    }
  }, [graphData]);

  const handleDialogClose = () => {
    setIsDialogOpen(false);
    setHighlightNodes(new Set());
    setHighlightLinks(new Set());
    if (graphRef.current) {
      graphRef.current.zoom(1, 500);
    }
  };


  const nodeCanvasObject = useCallback(
    (node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const knowledgeNode = node as KnowledgeNode;
      const label = knowledgeNode.name;
      const fontSize = 12 / globalScale;
      const nodeRadius = Math.sqrt(knowledgeNode.val || 10) * 2;

      // Determine if this node is highlighted
      const isHighlighted = highlightNodes.has(knowledgeNode.id);
      const isFiltered = filteredNodeIds !== null && !filteredNodeIds.has(knowledgeNode.id);
      const baseOpacity = isFiltered
        ? 0.04
        : highlightNodes.size === 0 || isHighlighted ? 0.45 : 0.08;

      // Draw outer glow effect for highlighted nodes
      if (isHighlighted && highlightNodes.size > 0) {
        ctx.beginPath();
        ctx.arc(node.x!, node.y!, nodeRadius + 8, 0, 2 * Math.PI);
        ctx.fillStyle = `${knowledgeNode.color}30`;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(node.x!, node.y!, nodeRadius + 4, 0, 2 * Math.PI);
        ctx.fillStyle = `${knowledgeNode.color}50`;
        ctx.fill();
      }

      // Draw node circle with transparency
      ctx.beginPath();
      ctx.arc(node.x!, node.y!, nodeRadius, 0, 2 * Math.PI);
      ctx.globalAlpha = baseOpacity;
      ctx.fillStyle = knowledgeNode.color;
      ctx.fill();
      ctx.globalAlpha = isHighlighted && highlightNodes.size > 0 ? 1 : 0.6;
      ctx.strokeStyle =
        isHighlighted && highlightNodes.size > 0
          ? "#ffffff"
          : knowledgeNode.color;
      ctx.lineWidth =
        isHighlighted && highlightNodes.size > 0
          ? 2 / globalScale
          : 1.5 / globalScale;
      ctx.stroke();

      // Draw label with bright color for visibility on dark background
      ctx.font = `${fontSize}px Inter, system-ui, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.globalAlpha = isFiltered ? 0.05 : (isHighlighted || highlightNodes.size === 0 ? 1 : 0.3);
      ctx.fillStyle = "#f0f0f0";
      ctx.fillText(label, node.x!, node.y! + nodeRadius + fontSize + 2);

      ctx.globalAlpha = 1;
    },
    [highlightNodes, filteredNodeIds],
  );

  const linkCanvasObject = useCallback(
    (link: LinkObject, ctx: CanvasRenderingContext2D) => {
      const source = link.source as NodeObject & KnowledgeNode;
      const target = link.target as NodeObject & KnowledgeNode;
      if (
        source.x == null ||
        source.y == null ||
        target.x == null ||
        target.y == null
      )
        return;

      const sourceRadius = Math.sqrt((source as KnowledgeNode).val || 10) * 2;
      const targetRadius = Math.sqrt((target as KnowledgeNode).val || 10) * 2;

      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist === 0) return;

      const ux = dx / dist;
      const uy = dy / dist;

      const linkKey = `${source.id}-${target.id}`;
      const isHighlighted = highlightLinks.has(linkKey);

      ctx.beginPath();
      ctx.moveTo(source.x + ux * sourceRadius, source.y + uy * sourceRadius);
      ctx.lineTo(target.x - ux * targetRadius, target.y - uy * targetRadius);
      ctx.strokeStyle =
        highlightLinks.size === 0
          ? "rgba(100, 120, 180, 0.25)"
          : isHighlighted
            ? "rgba(200, 220, 255, 0.9)"
            : "rgba(100, 120, 180, 0.08)";
      ctx.lineWidth = isHighlighted ? 2 : 1;
      ctx.stroke();
    },
    [highlightLinks],
  );

  // Handle loading and empty states
  if (isLoading) return <div className="flex h-full items-center justify-center text-gray-400">Loading graph...</div>;
  if (loadError) return <div className="flex h-full items-center justify-center text-gray-400">{loadError}</div>;
  if (graphData.nodes.length === 0) return (
    <div className="flex h-full flex-col items-center justify-center gap-2 text-gray-400">
      <p className="text-sm">No knowledge graph yet.</p>
      <p className="text-xs">Add and process some resources to build your graph.</p>
    </div>
  );

  return (
    <div
      ref={containerRef}
      className="relative h-full w-full overflow-hidden rounded-lg"
      style={{ backgroundColor: "#0a0a12" }}
    >
      {/* Graph Legend */}
      {categoryNodes.length > 0 && (
        <div
          className="absolute left-4 top-4 z-10 flex flex-col gap-2 rounded-lg border border-white/10 p-3 backdrop-blur-sm max-w-[45vw] sm:max-w-xs"
          style={{ backgroundColor: "rgba(15, 15, 25, 0.85)" }}
        >
          <p className="text-xs font-medium text-gray-200">
            Categories
            {selectedCategories.size > 0 && (
              <button
                onClick={() => setSelectedCategories(new Set())}
                className="ml-2 text-gray-400 hover:text-gray-200 text-xs underline"
              >
                Clear
              </button>
            )}
          </p>
          <div className="flex flex-wrap gap-2">
            {categoryNodes.map((cat, i) => {
              const color = CATEGORY_PALETTE[i % CATEGORY_PALETTE.length];
              const isActive = selectedCategories.has(cat.id);
              return (
                <Badge
                  key={cat.id}
                  variant="outline"
                  className="text-xs cursor-pointer transition-all"
                  style={{
                    borderColor: color,
                    color: color,
                    backgroundColor: isActive ? `${color}22` : "transparent",
                    opacity: selectedCategories.size > 0 && !isActive ? 0.45 : 1,
                  }}
                  onClick={() =>
                    setSelectedCategories((prev) => {
                      const next = new Set(prev);
                      if (next.has(cat.id)) next.delete(cat.id);
                      else next.add(cat.id);
                      return next;
                    })
                  }
                >
                  {cat.name}
                </Badge>
              );
            })}
          </div>
        </div>
      )}

      {/* Top-right controls — moved to bottom-right to avoid overlap with legend on mobile */}
      <div className="absolute right-4 bottom-4 z-10 flex flex-col items-end gap-2">
        <div
          className="rounded-lg border border-white/10 px-3 py-2 backdrop-blur-sm"
          style={{ backgroundColor: "rgba(15, 15, 25, 0.85)" }}
        >
          <p className="text-xs text-gray-400">Click on a node to explore</p>
        </div>
        <button
          onClick={handleReindex}
          disabled={isReindexing}
          className="rounded-lg border border-white/10 px-3 py-2 backdrop-blur-sm text-xs text-gray-400 hover:text-gray-200 hover:border-white/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          style={{ backgroundColor: "rgba(15, 15, 25, 0.85)" }}
        >
          {isReindexing ? "Reindexing…" : "Reindex Graph"}
        </button>
      </div>

      {/* Force Graph */}
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        nodeCanvasObject={nodeCanvasObject}
        nodePointerAreaPaint={(node, color, ctx) => {
          const knowledgeNode = node as KnowledgeNode;
          const nodeRadius = Math.sqrt(knowledgeNode.val || 10) * 2;
          ctx.beginPath();
          ctx.arc(node.x!, node.y!, nodeRadius + 5, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        onNodeClick={handleNodeClick}
        linkCanvasObject={linkCanvasObject}
        linkCanvasObjectMode={() => "replace"}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={(link) => {
          const linkKey = `${(link.source as NodeObject).id || link.source}-${(link.target as NodeObject).id || link.target}`;
          return highlightLinks.has(linkKey) ? 3 : 0;
        }}
        backgroundColor="transparent"
        cooldownTicks={150}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.4}
        onEngineStop={() => {
          if (hasCenteredRef.current) return;
          const rootNode = graphData.nodes.find((n) => n.node_type === "root");
          if (rootNode?.x != null && rootNode?.y != null) {
            hasCenteredRef.current = true;
            graphRef.current?.centerAt(rootNode.x, rootNode.y, 600);
          } else if (graphData.nodes.length > 0) {
            hasCenteredRef.current = true;
            graphRef.current?.zoomToFit(400, 50);
          }
        }}
      />

      {/* Node Detail Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={handleDialogClose}>
        <DialogContent className="flex flex-col overflow-hidden" style={{ maxWidth: "640px", width: "90vw", maxHeight: "80vh" }}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <span
                className="inline-block h-3 w-3 rounded-full"
                style={{ backgroundColor: selectedNode?.color }}
              />
              {selectedNode?.name}
            </DialogTitle>
            <DialogDescription>
              Category: {selectedNode?.category}
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4 overflow-hidden flex-1 min-h-0">
            {/* Connected Nodes */}
            <div className="shrink-0">
              <h4 className="mb-2 text-sm font-medium text-foreground">
                Connected Topics
              </h4>
              <div className="flex flex-wrap gap-2">
                {adjacentNodes.map((node) => {
                  const link = adjacentLinks.find(
                    (l) =>
                      (l.source === selectedNode?.id && l.target === node.id) ||
                      (l.target === selectedNode?.id && l.source === node.id),
                  );
                  return (
                    <Badge
                      key={node.id}
                      variant="secondary"
                      className="cursor-pointer transition-colors hover:bg-accent"
                      onClick={() => {
                        const nodeObj = graphData.nodes.find(
                          (n) => n.id === node.id,
                        );
                        if (nodeObj) {
                          handleNodeClick(nodeObj as unknown as NodeObject);
                        }
                      }}
                    >
                      <Link2 className="mr-1 h-3 w-3" />
                      {node.name}
                      <span className="ml-1 text-xs text-muted-foreground">
                        ({link?.relationship})
                      </span>
                    </Badge>
                  );
                })}
              </div>
            </div>

            {/* Resources */}
            <div className="flex flex-col flex-1 min-h-0">
              <h4 className="mb-2 text-sm font-medium text-foreground shrink-0">
                Related Resources
              </h4>
              <div className="flex-1 min-h-0 overflow-y-auto">
                <div className="w-full space-y-2 pr-1">
                  {resourcesLoading ? (
                    <div className="flex items-center justify-center py-4">
                      <div className="text-sm text-muted-foreground">Loading resources...</div>
                    </div>
                  ) : nodeResources.length > 0 ? (
                    nodeResources.map((resource) => (
                      <div
                        key={resource.id}
                        className="flex w-full min-w-0 items-start gap-3 overflow-hidden rounded-lg border border-border bg-card p-3"
                      >
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <Link
                            href={`/resources/${resource.id}`}
                            className="block text-sm font-medium text-foreground hover:underline"
                          >
                            {resource.title}
                          </Link>
                          {resource.url && (
                            <a
                              href={resource.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block truncate text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400"
                            >
                              {resource.url}
                            </a>
                          )}
                          <div className="mt-1 flex flex-wrap items-center gap-2 overflow-hidden">
                            <Badge
                              variant="outline"
                              className="text-xs capitalize"
                            >
                              {resource.status}
                            </Badge>
                            {resource.tags.map((tag) => (
                              <Badge
                                key={tag}
                                variant="secondary"
                                className="text-xs"
                              >
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="flex items-center justify-center py-4">
                      <div className="text-sm text-muted-foreground">No resources found for this node.</div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <Button variant="outline" onClick={handleDialogClose}>
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
