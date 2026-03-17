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
  ExternalLink,
  FileText,
  Link2,
  BookOpen,
  Video,
  Code,
} from "lucide-react";

// Types for the graph
interface Resource {
  id: string;
  title: string;
  type: "article" | "video" | "document" | "code" | "book";
  url: string;
  description: string;
}

interface KnowledgeNode extends NodeObject {
  id: string;
  name: string;
  category: string;
  color: string;
  resources: Resource[];
  val?: number;
}

interface KnowledgeLink extends LinkObject {
  source: string;
  target: string;
  relationship: string;
}

// Sample knowledge graph data
const knowledgeData = {
  nodes: [
    {
      id: "ml",
      name: "Machine Learning",
      category: "AI",
      color: "#60a5fa",
      val: 25,
      resources: [
        {
          id: "r1",
          title: "Introduction to ML",
          type: "article" as const,
          url: "/app/resources/ml-intro",
          description: "A comprehensive guide to machine learning fundamentals",
        },
        {
          id: "r2",
          title: "ML with Python",
          type: "video" as const,
          url: "/app/resources/ml-python",
          description: "Video course on implementing ML algorithms",
        },
        {
          id: "r3",
          title: "Scikit-learn Docs",
          type: "document" as const,
          url: "/app/resources/sklearn",
          description: "Official documentation for scikit-learn",
        },
      ],
    },
    {
      id: "dl",
      name: "Deep Learning",
      category: "AI",
      color: "#a78bfa",
      val: 22,
      resources: [
        {
          id: "r4",
          title: "Neural Networks Explained",
          type: "article" as const,
          url: "/app/resources/nn-explained",
          description: "Understanding neural network architectures",
        },
        {
          id: "r5",
          title: "PyTorch Tutorial",
          type: "code" as const,
          url: "/app/resources/pytorch",
          description: "Hands-on PyTorch examples",
        },
      ],
    },
    {
      id: "nlp",
      name: "Natural Language Processing",
      category: "AI",
      color: "#22d3ee",
      val: 20,
      resources: [
        {
          id: "r6",
          title: "NLP Fundamentals",
          type: "book" as const,
          url: "/app/resources/nlp-book",
          description: "Comprehensive NLP textbook",
        },
        {
          id: "r7",
          title: "Transformers Guide",
          type: "article" as const,
          url: "/app/resources/transformers",
          description: "Understanding transformer architecture",
        },
      ],
    },
    {
      id: "cv",
      name: "Computer Vision",
      category: "AI",
      color: "#34d399",
      val: 18,
      resources: [
        {
          id: "r8",
          title: "OpenCV Tutorial",
          type: "video" as const,
          url: "/app/resources/opencv",
          description: "Getting started with OpenCV",
        },
        {
          id: "r9",
          title: "Image Classification",
          type: "code" as const,
          url: "/app/resources/img-class",
          description: "Build your first image classifier",
        },
      ],
    },
    {
      id: "data",
      name: "Data Science",
      category: "Analytics",
      color: "#fbbf24",
      val: 24,
      resources: [
        {
          id: "r10",
          title: "Data Analysis with Pandas",
          type: "article" as const,
          url: "/app/resources/pandas",
          description: "Master data manipulation with Pandas",
        },
        {
          id: "r11",
          title: "Statistical Methods",
          type: "book" as const,
          url: "/app/resources/stats",
          description: "Statistics for data science",
        },
      ],
    },
    {
      id: "viz",
      name: "Data Visualization",
      category: "Analytics",
      color: "#f472b6",
      val: 16,
      resources: [
        {
          id: "r12",
          title: "D3.js Fundamentals",
          type: "code" as const,
          url: "/app/resources/d3",
          description: "Interactive visualizations with D3",
        },
        {
          id: "r13",
          title: "Chart Design Principles",
          type: "article" as const,
          url: "/app/resources/charts",
          description: "Best practices for data viz",
        },
      ],
    },
    {
      id: "python",
      name: "Python",
      category: "Programming",
      color: "#818cf8",
      val: 28,
      resources: [
        {
          id: "r14",
          title: "Python Basics",
          type: "video" as const,
          url: "/app/resources/python-basics",
          description: "Learn Python from scratch",
        },
        {
          id: "r15",
          title: "Advanced Python",
          type: "book" as const,
          url: "/app/resources/adv-python",
          description: "Master advanced Python concepts",
        },
      ],
    },
    {
      id: "math",
      name: "Mathematics",
      category: "Foundations",
      color: "#f87171",
      val: 20,
      resources: [
        {
          id: "r16",
          title: "Linear Algebra",
          type: "video" as const,
          url: "/app/resources/linear-algebra",
          description: "Essential linear algebra for ML",
        },
        {
          id: "r17",
          title: "Calculus for ML",
          type: "article" as const,
          url: "/app/resources/calculus",
          description: "Calculus concepts in machine learning",
        },
      ],
    },
    {
      id: "stats",
      name: "Statistics",
      category: "Foundations",
      color: "#fb923c",
      val: 18,
      resources: [
        {
          id: "r18",
          title: "Probability Theory",
          type: "book" as const,
          url: "/app/resources/probability",
          description: "Foundations of probability",
        },
        {
          id: "r19",
          title: "Bayesian Statistics",
          type: "article" as const,
          url: "/app/resources/bayesian",
          description: "Introduction to Bayesian methods",
        },
      ],
    },
  ],
  links: [
    { source: "ml", target: "dl", relationship: "foundation for" },
    { source: "ml", target: "nlp", relationship: "enables" },
    { source: "ml", target: "cv", relationship: "enables" },
    { source: "dl", target: "nlp", relationship: "powers" },
    { source: "dl", target: "cv", relationship: "powers" },
    { source: "python", target: "ml", relationship: "used in" },
    { source: "python", target: "data", relationship: "used in" },
    { source: "data", target: "ml", relationship: "feeds into" },
    { source: "data", target: "viz", relationship: "enables" },
    { source: "math", target: "ml", relationship: "foundation of" },
    { source: "math", target: "dl", relationship: "foundation of" },
    { source: "stats", target: "ml", relationship: "foundation of" },
    { source: "stats", target: "data", relationship: "foundation of" },
    { source: "nlp", target: "cv", relationship: "combines with" },
  ],
};

const resourceIcons = {
  article: FileText,
  video: Video,
  document: FileText,
  code: Code,
  book: BookOpen,
};

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

  const handleNodeClick = useCallback((node: NodeObject) => {
    const knowledgeNode = node as KnowledgeNode;
    setSelectedNode(knowledgeNode);

    // Find adjacent nodes and links
    const adjLinks = knowledgeData.links.filter(
      (link) =>
        link.source === knowledgeNode.id || link.target === knowledgeNode.id,
    );
    setAdjacentLinks(adjLinks);

    const adjNodeIds = new Set<string>();
    adjLinks.forEach((link) => {
      if (link.source === knowledgeNode.id) adjNodeIds.add(link.target);
      if (link.target === knowledgeNode.id) adjNodeIds.add(link.source);
    });

    const adjNodes = knowledgeData.nodes.filter((n) => adjNodeIds.has(n.id));
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

    setIsDialogOpen(true);

    // Zoom to the node
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 500);
      graphRef.current.zoom(2, 500);
    }
  }, []);

  const handleDialogClose = () => {
    setIsDialogOpen(false);
    setHighlightNodes(new Set());
    setHighlightLinks(new Set());
    if (graphRef.current) {
      graphRef.current.zoom(1, 500);
    }
  };

  const navigateToResource = (url: string) => {
    window.location.href = url;
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
        graphData={knowledgeData}
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
        <DialogContent className="max-w-lg">
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
                        const nodeObj = knowledgeData.nodes.find(
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
                  {selectedNode?.resources.map((resource) => {
                    const Icon = resourceIcons[resource.type];
                    return (
                      <div
                        key={resource.id}
                        className="group flex cursor-pointer items-start gap-3 rounded-lg border border-border bg-card p-3 transition-colors hover:bg-accent"
                        onClick={() => navigateToResource(resource.url)}
                      >
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                          <Icon className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-foreground group-hover:underline">
                              {resource.title}
                            </p>
                            <ExternalLink className="h-3 w-3 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {resource.description}
                          </p>
                          <Badge
                            variant="outline"
                            className="mt-1 text-xs capitalize"
                          >
                            {resource.type}
                          </Badge>
                        </div>
                      </div>
                    );
                  })}
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
