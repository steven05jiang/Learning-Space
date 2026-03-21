import { rest } from 'msw'

export const graphHandlers = [
  rest.get('/api/graph', (req, res, ctx) => {
    return res(
      ctx.json({ nodes: [{ id: 'node-1', label: 'AI', level: 'current' }], edges: [] })
    )
  }),
  rest.post('/api/graph/expand', (req, res, ctx) => {
    return res(
      ctx.json({ nodes: [{ id: 'node-2', label: 'Testing', level: 'child' }], edges: [{ source: 'node-1', target: 'node-2', weight: 1 }] })
    )
  }),
  rest.get('/api/graph/nodes/:id/resources', (req, res, ctx) => {
    return res(
      ctx.json({ items: [{ id: 'uuid-1', title: 'Mock Resource', status: 'READY' }] })
    )
  }),
]