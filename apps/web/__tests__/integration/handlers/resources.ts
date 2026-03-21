import { rest } from 'msw'

export const resourceHandlers = [
  rest.get('/api/resources', (req, res, ctx) => {
    return res(
      ctx.json({
        items: [{ id: 'uuid-1', title: 'Mock Resource', status: 'READY', tags: ['AI'], original_content: 'https://example.com', content_type: 'url' }],
        total: 1,
      })
    )
  }),
  rest.post('/api/resources', (req, res, ctx) => {
    return res(
      ctx.status(202),
      ctx.json({ id: 'uuid-new', status: 'PENDING' })
    )
  }),
  rest.get('/api/resources/:id', (req, res, ctx) => {
    return res(
      ctx.json({ id: 'uuid-1', title: 'Mock Resource', status: 'READY', tags: ['AI'], summary: 'A test summary.', original_content: 'https://example.com', content_type: 'url' })
    )
  }),
  rest.patch('/api/resources/:id', (req, res, ctx) => {
    return res(
      ctx.json({ id: 'uuid-1', title: 'Updated Title' })
    )
  }),
  rest.delete('/api/resources/:id', (req, res, ctx) => {
    return res(ctx.status(204))
  }),
]