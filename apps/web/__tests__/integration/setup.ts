import { setupServer } from 'msw/node'
import { authHandlers } from './handlers/auth'
import { resourceHandlers } from './handlers/resources'
import { graphHandlers } from './handlers/graph'
import { chatHandlers } from './handlers/chat'

export const server = setupServer(
  ...authHandlers,
  ...resourceHandlers,
  ...graphHandlers,
  ...chatHandlers,
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())