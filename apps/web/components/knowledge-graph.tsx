"use client";

import { useCallback, useRef, useState, useEffect } from "react";
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
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  FileText,
  Link2,
} from "lucide-react";

// API response types
interface ApiGraphNode {
  id: string;
  label: string;
  level: string; // "root", "current", "child", "parent"
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
  const nodes: KnowledgeNode[] = data.nodes.map((n) => ({
    id: n.id,
    name: n.label,
    category: n.level,
    color: colorByLevel[n.level] ?? '#818cf8',
    val: 15,
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
  const newNodes = newData.nodes
    .filter((n) => !existingIds.has(n.id))
    .map((n) => ({
      id: n.id,
      name: n.label,
      category: n.level,
      color: colorByLevel[n.level] ?? '#818cf8',
      val: 15
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

  // Handle container resize (including when chat panel opens/closes)
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
        graphRef.current?.centerAt(0, 0, 300);
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
      const baseOpacity =
        highlightNodes.size === 0 || isHighlighted ? 0.45 : 0.08;

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
      ctx.globalAlpha = isHighlighted || highlightNodes.size === 0 ? 1 : 0.3;
      ctx.fillStyle = "#f0f0f0";
      ctx.fillText(label, node.x!, node.y! + nodeRadius + fontSize + 2);

      ctx.globalAlpha = 1;
    },
    [highlightNodes],
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
      <div
        className="absolute left-4 top-4 z-10 flex flex-col gap-2 rounded-lg border border-white/10 p-3 backdrop-blur-sm"
        style={{ backgroundColor: "rgba(15, 15, 25, 0.85)" }}
      >
        <p className="text-xs font-medium text-gray-200">Categories</p>
        <div className="flex flex-wrap gap-2">
          {["AI", "Analytics", "Programming", "Foundations"].map((cat, i) => (
            <Badge
              key={cat}
              variant="outline"
              className="text-xs border-opacity-60"
              style={{
                borderColor: ["#60a5fa", "#fbbf24", "#818cf8", "#f87171"][i],
                color: ["#60a5fa", "#fbbf24", "#818cf8", "#f87171"][i],
                backgroundColor: "transparent",
              }}
            >
              {cat}
            </Badge>
          ))}
        </div>
      </div>

      {/* Instructions */}
      <div
        className="absolute right-4 top-4 z-10 rounded-lg border border-white/10 px-3 py-2 backdrop-blur-sm"
        style={{ backgroundColor: "rgba(15, 15, 25, 0.85)" }}
      >
        <p className="text-xs text-gray-400">Click on a node to explore</p>
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
        cooldownTicks={100}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
      />

      {/* Node Detail Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={handleDialogClose}>
        <DialogContent className="overflow-hidden" style={{ maxWidth: "320px", maxHeight: "240px" }}>
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

          <div className="space-y-4">
            {/* Connected Nodes */}
            <div>
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
            <div>
              <h4 className="mb-2 text-sm font-medium text-foreground">
                Related Resources
              </h4>
              <ScrollArea className="h-[200px]">
                <div className="space-y-2 pr-4">
                  {resourcesLoading ? (
                    <div className="flex items-center justify-center py-4">
                      <div className="text-sm text-muted-foreground">Loading resources...</div>
                    </div>
                  ) : nodeResources.length > 0 ? (
                    nodeResources.map((resource) => (
                      <div
                        key={resource.id}
                        className="flex items-start gap-3 rounded-lg border border-border bg-card p-3"
                      >
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-foreground overflow-hidden text-ellipsis whitespace-nowrap">
                            {resource.title}
                          </p>
                          {resource.url && (
                            <a
                              href={resource.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-blue-600 hover:text-blue-800 overflow-hidden text-ellipsis whitespace-nowrap block"
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
              </ScrollArea>
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
