import { rest } from 'msw'

export const authHandlers = [
  rest.get('/api/auth/me', (req, res, ctx) => {
    return res(
      ctx.json({
        id: 'user-1',
        display_name: 'Test User',
        email: 'test@example.com',
        accounts: [{ provider: 'twitter', external_id: 'twitter-123' }],
      })
    )
  }),
  rest.post('/api/auth/logout', (req, res, ctx) => {
    return res(ctx.status(204))
  }),
]