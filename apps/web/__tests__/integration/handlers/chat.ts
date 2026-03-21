import { rest } from 'msw'

export const chatHandlers = [
  rest.post('/api/chat', (req, res, ctx) => {
    return res(
      ctx.json({ conversation_id: 'conv-1', message: { role: 'assistant', content: 'Mock response.' } })
    )
  }),
  rest.get('/api/chat/conversations', (req, res, ctx) => {
    return res(
      ctx.json({ items: [{ id: 'conv-1', title: 'Test Conversation', created_at: '2026-03-20T00:00:00Z' }] })
    )
  }),
]