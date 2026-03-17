import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import ResourcesPage from '../app/resources/page'

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000'

const mockPush = jest.fn()

beforeEach(() => {
  ;(useRouter as jest.Mock).mockReturnValue({ push: mockPush })
  jest.spyOn(console, 'error').mockImplementation((error) => {
    if (!(error?.message === 'Not implemented: navigation (except hash changes)')) {
      console.warn(error)
    }
  })
})

describe('ResourcesPage', () => {
  beforeEach(() => {
    localStorage.clear()
    ;(fetch as jest.MockedFunction<typeof fetch>).mockClear()
    mockPush.mockClear()
    jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {})
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => null)
    jest.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('redirects to login if no auth token', () => {
    render(<ResourcesPage />)
    expect(mockPush).toHaveBeenCalledWith('/login')
  })

  it('redirects to login if invalid user info', () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return 'invalid-json'
      return null
    })
    render(<ResourcesPage />)
    expect(localStorage.removeItem).toHaveBeenCalledWith('user_info')
    expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token')
    expect(mockPush).toHaveBeenCalledWith('/login')
  })

  it('renders empty state when no resources', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({ id: '1', email: 'test@example.com', display_name: 'Test User' })
      return null
    })

    ;(fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ items: [], total: 0, limit: 20, offset: 0 }),
    })

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(screen.getByText('No resources yet')).toBeInTheDocument()
    })

    expect(screen.getByText('Get started by submitting your first learning resource.')).toBeInTheDocument()
  })

  it('renders resources when loaded', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({ id: '1', email: 'test@example.com', display_name: 'Test User' })
      return null
    })

    const mockResources = [
      {
        id: '1',
        url: 'https://example.com/article',
        title: 'Example Article',
        summary: 'A test article',
        tags: ['test', 'example'],
        status: 'READY' as const,
        created_at: '2024-01-01T10:00:00Z',
      },
      {
        id: '2',
        url: 'https://another.com/post',
        title: 'Another Post',
        summary: 'Another test post',
        tags: ['blog'],
        status: 'PROCESSING' as const,
        created_at: '2024-01-02T11:00:00Z',
      },
    ]

    ;(fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ items: mockResources, total: 2, limit: 20, offset: 0 }),
    })

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(screen.getByText('Example Article')).toBeInTheDocument()
    })

    expect(screen.getByText('Another Post')).toBeInTheDocument()
    expect(screen.getByText('Ready')).toBeInTheDocument()
    expect(screen.getByText('Processing')).toBeInTheDocument()
    expect(screen.getByText('test')).toBeInTheDocument()
    expect(screen.getByText('example')).toBeInTheDocument()
    expect(screen.getByText('blog')).toBeInTheDocument()
  })

  it('calls API with correct URL and auth header', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({ id: '1', email: 'test@example.com', display_name: 'Test User' })
      return null
    })

    ;(fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ items: [], total: 0, limit: 20, offset: 0 }),
    })

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/resources?limit=20&offset=0',
        expect.objectContaining({
          headers: expect.objectContaining({ Authorization: 'Bearer mock-token' }),
        })
      )
    })
  })

  it('redirects to login on 401 response', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({ id: '1', email: 'test@example.com', display_name: 'Test User' })
      return null
    })

    ;(fetch as jest.Mock).mockResolvedValue({ ok: false, status: 401 })

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('user_info')
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  it('shows error message on API failure', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({ id: '1', email: 'test@example.com', display_name: 'Test User' })
      return null
    })

    ;(fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({}),
    })

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(
        screen.getByText('Failed to fetch resources: Internal Server Error')
      ).toBeInTheDocument()
    })
  })

  it('navigates to Add Resource on button click', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({ id: '1', email: 'test@example.com', display_name: 'Test User' })
      return null
    })

    ;(fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ items: [], total: 0, limit: 20, offset: 0 }),
    })

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(screen.getByText('No resources yet')).toBeInTheDocument()
    })

    const addButtons = screen.getAllByRole('button', { name: /add resource/i })
    fireEvent.click(addButtons[0])
    expect(mockPush).toHaveBeenCalledWith('/resources/new')
  })

  it('displays all resource status badge labels', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({ id: '1', email: 'test@example.com', display_name: 'Test User' })
      return null
    })

    // Use distinct titles so badge text is unambiguous
    const mockResources = [
      { id: '1', url: 'https://ready.com',      title: 'Article One',   summary: '', tags: [], status: 'READY' as const,      created_at: '2024-01-01T10:00:00Z' },
      { id: '2', url: 'https://processing.com', title: 'Article Two',   summary: '', tags: [], status: 'PROCESSING' as const, created_at: '2024-01-01T10:00:00Z' },
      { id: '3', url: 'https://pending.com',    title: 'Article Three', summary: '', tags: [], status: 'PENDING' as const,    created_at: '2024-01-01T10:00:00Z' },
      { id: '4', url: 'https://failed.com',     title: 'Article Four',  summary: '', tags: [], status: 'FAILED' as const,     created_at: '2024-01-01T10:00:00Z' },
    ]

    ;(fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ items: mockResources, total: 4, limit: 20, offset: 0 }),
    })

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(screen.getByText('Article One')).toBeInTheDocument()
    })

    expect(screen.getByText('Ready')).toBeInTheDocument()
    expect(screen.getByText('Processing')).toBeInTheDocument()
    expect(screen.getByText('Pending')).toBeInTheDocument()
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })
})
