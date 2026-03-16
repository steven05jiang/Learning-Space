import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import ResourcesPage from '../app/resources/page'

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

// Mock environment variable
process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000'

const mockPush = jest.fn()

beforeEach(() => {
  ;(useRouter as jest.Mock).mockReturnValue({
    push: mockPush,
  })

  // Suppress JSDOM navigation errors globally
  jest.spyOn(console, 'error').mockImplementation((error) => {
    if (!(error && error.message === 'Not implemented: navigation (except hash changes)')) {
      console.warn(error)
    }
  })
})

describe('ResourcesPage', () => {
  beforeEach(() => {
    localStorage.clear()
    ;(fetch as jest.MockedFunction<typeof fetch>).mockClear()
    mockPush.mockClear()

    // Mock localStorage methods as spies
    jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {})
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => null)
    jest.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('redirects to login if no auth token', () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => null)

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
      if (key === 'user_info') return JSON.stringify({
        id: '1',
        email: 'test@example.com',
        display_name: 'Test User'
      })
      return null
    })

    const mockResponse = {
      ok: true,
      json: jest.fn(() => Promise.resolve({
        items: [],
        total: 0,
        limit: 20,
        offset: 0
      }))
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(screen.getByText('No resources yet')).toBeInTheDocument()
    })

    expect(screen.getByText('Start building your learning collection by adding your first resource.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add Your First Resource' })).toBeInTheDocument()
  })

  it('renders resources list when resources exist', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({
        id: '1',
        email: 'test@example.com',
        display_name: 'Test User'
      })
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
        created_at: '2024-01-01T10:00:00Z'
      },
      {
        id: '2',
        url: 'https://another.com/post',
        title: 'Another Post',
        summary: 'Another test post',
        tags: ['blog'],
        status: 'PROCESSING' as const,
        created_at: '2024-01-02T11:00:00Z'
      }
    ]

    const mockResponse = {
      ok: true,
      json: jest.fn(() => Promise.resolve({
        items: mockResources,
        total: 2,
        limit: 20,
        offset: 0
      }))
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(screen.getByText('Example Article')).toBeInTheDocument()
    })

    expect(screen.getByText('Another Post')).toBeInTheDocument()
    expect(screen.getByText('READY')).toBeInTheDocument()
    expect(screen.getByText('PROCESSING')).toBeInTheDocument()
    expect(screen.getByText('test')).toBeInTheDocument()
    expect(screen.getByText('example')).toBeInTheDocument()
    expect(screen.getByText('blog')).toBeInTheDocument()
  })

  it('fetches resources without limit parameter', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({
        id: '1',
        email: 'test@example.com',
        display_name: 'Test User'
      })
      return null
    })

    const mockResponse = {
      ok: true,
      json: jest.fn(() => Promise.resolve({
        items: [],
        total: 0,
        limit: 20,
        offset: 0
      }))
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/resources/', {
        headers: {
          'Authorization': 'Bearer mock-token'
        }
      })
    })

    expect(fetch).not.toHaveBeenCalledWith(expect.stringContaining('limit='), expect.any(Object))
  })

  it('redirects to login on 401 response', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({
        id: '1',
        email: 'test@example.com',
        display_name: 'Test User'
      })
      return null
    })

    const mockResponse = {
      ok: false,
      status: 401
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

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
      if (key === 'user_info') return JSON.stringify({
        id: '1',
        email: 'test@example.com',
        display_name: 'Test User'
      })
      return null
    })

    const mockResponse = {
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: jest.fn(() => Promise.resolve({ detail: 'Server error' }))
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(screen.getByText('Server error')).toBeInTheDocument()
    })

    // Check for retry button
    const retryButton = screen.getByText('Try again')
    expect(retryButton).toBeInTheDocument()
  })

  it('retries loading resources when retry button is clicked', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({
        id: '1',
        email: 'test@example.com',
        display_name: 'Test User'
      })
      return null
    })

    // First call fails, second succeeds
    const mockFailResponse = {
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: jest.fn(() => Promise.resolve({ detail: 'Server error' }))
    }
    const mockSuccessResponse = {
      ok: true,
      json: jest.fn(() => Promise.resolve({
        items: [],
        total: 0,
        limit: 20,
        offset: 0
      }))
    }
    ;(fetch as jest.Mock).mockResolvedValueOnce(mockFailResponse).mockResolvedValueOnce(mockSuccessResponse)

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(screen.getByText('Server error')).toBeInTheDocument()
    })

    const retryButton = screen.getByText('Try again')
    fireEvent.click(retryButton)

    await waitFor(() => {
      expect(screen.getByText('No resources yet')).toBeInTheDocument()
    })

    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it('shows loading state during resource fetch', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({
        id: '1',
        email: 'test@example.com',
        display_name: 'Test User'
      })
      return null
    })

    const mockResponse = {
      ok: true,
      json: jest.fn(() => new Promise(resolve =>
        setTimeout(() => resolve({
          items: [],
          total: 0,
          limit: 20,
          offset: 0
        }), 100)
      ))
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

    render(<ResourcesPage />)

    expect(screen.getByText('Loading resources...')).toBeInTheDocument()
  })

  it('displays resource status badges with correct colors', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({
        id: '1',
        email: 'test@example.com',
        display_name: 'Test User'
      })
      return null
    })

    const mockResources = [
      { id: '1', url: 'https://ready.com', title: 'Ready', summary: '', tags: [], status: 'READY' as const, created_at: '2024-01-01T10:00:00Z' },
      { id: '2', url: 'https://processing.com', title: 'Processing', summary: '', tags: [], status: 'PROCESSING' as const, created_at: '2024-01-01T10:00:00Z' },
      { id: '3', url: 'https://pending.com', title: 'Pending', summary: '', tags: [], status: 'PENDING' as const, created_at: '2024-01-01T10:00:00Z' },
      { id: '4', url: 'https://failed.com', title: 'Failed', summary: '', tags: [], status: 'FAILED' as const, created_at: '2024-01-01T10:00:00Z' }
    ]

    const mockResponse = {
      ok: true,
      json: jest.fn(() => Promise.resolve({
        items: mockResources,
        total: 4,
        limit: 20,
        offset: 0
      }))
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(screen.getByText('Ready')).toBeInTheDocument()
    })

    const readyBadge = screen.getByText('READY')
    const processingBadge = screen.getByText('PROCESSING')
    const pendingBadge = screen.getByText('PENDING')
    const failedBadge = screen.getByText('FAILED')

    expect(readyBadge).toHaveClass('bg-green-100', 'text-green-800')
    expect(processingBadge).toHaveClass('bg-blue-100', 'text-blue-800')
    expect(pendingBadge).toHaveClass('bg-yellow-100', 'text-yellow-800')
    expect(failedBadge).toHaveClass('bg-red-100', 'text-red-800')
  })

  it('handles navigation correctly', async () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'auth_token') return 'mock-token'
      if (key === 'user_info') return JSON.stringify({
        id: '1',
        email: 'test@example.com',
        display_name: 'Test User'
      })
      return null
    })

    const mockResponse = {
      ok: true,
      json: jest.fn(() => Promise.resolve({
        items: [],
        total: 0,
        limit: 20,
        offset: 0
      }))
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

    render(<ResourcesPage />)

    await waitFor(() => {
      expect(screen.getByText('No resources yet')).toBeInTheDocument()
    })

    const addResourceButtons = screen.getAllByText(/Add.*Resource/)

    // Test header Add Resource button
    fireEvent.click(addResourceButtons[0])
    expect(mockPush).toHaveBeenCalledWith('/resources/new')

    mockPush.mockClear()

    // Test dashboard navigation
    const dashboardButton = screen.getByText('Dashboard')
    fireEvent.click(dashboardButton)
    expect(mockPush).toHaveBeenCalledWith('/dashboard')
  })
})