// Graph mock data and utilities
export const mockGraphData = {
  nodes: [
    { id: 'node_1', label: 'Node 1', type: 'resource', properties: { title: 'Test Resource 1' } },
    { id: 'node_2', label: 'Node 2', type: 'tag', properties: { name: 'test' } },
    { id: 'node_3', label: 'Node 3', type: 'resource', properties: { title: 'Test Resource 2' } },
  ],
  edges: [
    { id: 'edge_1', source: 'node_1', target: 'node_2', type: 'HAS_TAG' },
    { id: 'edge_2', source: 'node_3', target: 'node_2', type: 'HAS_TAG' },
  ],
};

export const graphMockHandlers = {
  getGraph: (filters?: { nodeType?: string; depth?: number }) =>
    Promise.resolve({
      ok: true,
      json: () => {
        let filteredData = { ...mockGraphData };

        if (filters?.nodeType) {
          filteredData.nodes = mockGraphData.nodes.filter(node => node.type === filters.nodeType);
          const nodeIds = new Set(filteredData.nodes.map(n => n.id));
          filteredData.edges = mockGraphData.edges.filter(edge =>
            nodeIds.has(edge.source) && nodeIds.has(edge.target)
          );
        }

        return Promise.resolve(filteredData);
      },
    }),

  getSubgraph: (nodeId: string) =>
    Promise.resolve({
      ok: true,
      json: () => {
        const startNode = mockGraphData.nodes.find(n => n.id === nodeId);
        if (!startNode) {
          return Promise.resolve({ error: 'Node not found' });
        }

        const connectedEdges = mockGraphData.edges.filter(e =>
          e.source === nodeId || e.target === nodeId
        );

        const neighborIds = new Set();
        connectedEdges.forEach(edge => {
          neighborIds.add(edge.source);
          neighborIds.add(edge.target);
        });

        const subgraphNodes = mockGraphData.nodes.filter(n => neighborIds.has(n.id));

        return Promise.resolve({
          nodes: subgraphNodes,
          edges: connectedEdges,
        });
      },
    }),

  searchNodes: (query: string) =>
    Promise.resolve({
      ok: true,
      json: () => {
        if (!query) {
          return Promise.resolve({ nodes: [], edges: [] });
        }

        const matchingNodes = mockGraphData.nodes.filter(node =>
          node.label.toLowerCase().includes(query.toLowerCase()) ||
          (node.properties.title && node.properties.title.toLowerCase().includes(query.toLowerCase())) ||
          (node.properties.name && node.properties.name.toLowerCase().includes(query.toLowerCase()))
        );

        const matchingNodeIds = new Set(matchingNodes.map(n => n.id));
        const matchingEdges = mockGraphData.edges.filter(edge =>
          matchingNodeIds.has(edge.source) && matchingNodeIds.has(edge.target)
        );

        return Promise.resolve({
          nodes: matchingNodes,
          edges: matchingEdges,
        });
      },
    }),

  updateNode: (nodeId: string, data: any) =>
    Promise.resolve({
      ok: true,
      json: () => {
        const node = mockGraphData.nodes.find(n => n.id === nodeId);
        if (!node) {
          return Promise.resolve({ error: 'Node not found' });
        }

        return Promise.resolve({
          ...node,
          properties: { ...node.properties, ...data.properties },
        });
      },
    }),
};