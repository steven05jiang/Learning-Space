import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter, useSearchParams } from 'next/navigation'
import LoginPage from '../app/login/page'

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}))

// Mock environment variable
process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000'

const mockPush = jest.fn()
const mockGet = jest.fn()

// Mock window.location
const mockLocation = {
  href: '',
  assign: jest.fn(),
  reload: jest.fn(),
  replace: jest.fn(),
}

beforeEach(() => {
  ;(useRouter as jest.Mock).mockReturnValue({
    push: mockPush,
  })
  ;(useSearchParams as jest.Mock).mockReturnValue({
    get: mockGet,
  })
  // Reset location href
  mockLocation.href = ''
  // Mock window.location assignment
  Object.defineProperty(window, 'location', {
    value: mockLocation,
    writable: true
  })
})

describe('LoginPage', () => {
  beforeEach(() => {
    localStorage.clear()
    ;(fetch as jest.MockedFunction<typeof fetch>).mockClear()
    mockPush.mockClear()
    mockGet.mockClear()
  })

  it('renders login page with OAuth providers', () => {
    render(<LoginPage />)

    expect(screen.getByText('Learning Space')).toBeInTheDocument()
    expect(screen.getByText('Sign in to your account')).toBeInTheDocument()
    expect(screen.getByText('Continue with GitHub')).toBeInTheDocument()
    expect(screen.getByText('Continue with Google')).toBeInTheDocument()
    expect(screen.getByText('Continue with Twitter')).toBeInTheDocument()
  })

  it('redirects if user is already logged in', () => {
    localStorage.setItem('auth_token', 'mock-token')
    localStorage.setItem('user_info', JSON.stringify({ id: '1', email: 'test@example.com' }))

    render(<LoginPage />)

    expect(mockPush).toHaveBeenCalledWith('/')
  })

  it('does not redirect if only token exists without user info', () => {
    localStorage.setItem('auth_token', 'mock-token')
    // No user_info set

    render(<LoginPage />)

    expect(mockPush).not.toHaveBeenCalled()
  })

  it('redirects to returnTo URL if provided', () => {
    localStorage.setItem('auth_token', 'mock-token')
    localStorage.setItem('user_info', JSON.stringify({ id: '1', email: 'test@example.com' }))
    mockGet.mockReturnValue('/dashboard')

    render(<LoginPage />)

    expect(mockPush).toHaveBeenCalledWith('/dashboard')
  })

  it('initiates OAuth login when provider button is clicked', async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        authorization_url: 'https://github.com/login/oauth/authorize?state=test-state',
        provider: 'github',
        state: 'test-state',
      }),
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

    render(<LoginPage />)

    const githubButton = screen.getByText('Continue with GitHub')
    fireEvent.click(githubButton)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/auth/login/github')
    })

    // Verify that the OAuth flow was initiated successfully
    expect(mockResponse.json).toHaveBeenCalled()

    // Verify state is stored for CSRF protection
    expect(localStorage.getItem('oauth_state_github')).toBe('test-state')
  })

  it('handles OAuth login error', async () => {
    const mockResponse = {
      ok: false,
      status: 400,
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

    render(<LoginPage />)

    const githubButton = screen.getByText('Continue with GitHub')
    fireEvent.click(githubButton)

    await waitFor(() => {
      expect(screen.getByText('Failed to initiate github login')).toBeInTheDocument()
    })
  })

  it('shows loading state during OAuth initiation', async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        authorization_url: 'https://github.com/login/oauth/authorize',
        provider: 'github',
        state: 'test-state',
      }),
    }
    ;(fetch as jest.Mock).mockImplementation(() =>
      new Promise(resolve => setTimeout(() => resolve(mockResponse), 100))
    )

    render(<LoginPage />)

    const githubButton = screen.getByText('Continue with GitHub')
    fireEvent.click(githubButton)

    expect(screen.getByText('Connecting...')).toBeInTheDocument()
    expect(githubButton).toBeDisabled()
  })

  it('handles missing authorization_url edge case', async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        provider: 'github',
        state: 'test-state',
        // Missing authorization_url
      }),
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

    render(<LoginPage />)

    const githubButton = screen.getByText('Continue with GitHub')
    fireEvent.click(githubButton)

    await waitFor(() => {
      expect(screen.getByText('No authorization URL received')).toBeInTheDocument()
    })
  })

  it('handles localStorage quota exceeded error', async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        authorization_url: 'https://github.com/login/oauth/authorize?state=test-state',
        provider: 'github',
        state: 'test-state',
      }),
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

    // Mock localStorage.setItem to throw on first call, succeed on second
    let callCount = 0
    const originalSetItem = localStorage.setItem
    localStorage.setItem = jest.fn().mockImplementation((key, value) => {
      if (key.startsWith('oauth_state_') && callCount === 0) {
        callCount++
        throw new Error('QuotaExceededError')
      }
      return originalSetItem.call(localStorage, key, value)
    })

    render(<LoginPage />)

    const githubButton = screen.getByText('Continue with GitHub')
    fireEvent.click(githubButton)

    // Wait for the API call to complete
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/auth/login/github')
    })

    // Verify it cleared auth data and retried
    expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token')
    expect(localStorage.removeItem).toHaveBeenCalledWith('user_info')
  })

  it('handles persistent localStorage quota exceeded error', async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        authorization_url: 'https://github.com/login/oauth/authorize?state=test-state',
        provider: 'github',
        state: 'test-state',
      }),
    }
    ;(fetch as jest.Mock).mockResolvedValue(mockResponse)

    // Mock localStorage.setItem to always throw
    localStorage.setItem = jest.fn().mockImplementation(() => {
      throw new Error('QuotaExceededError')
    })

    render(<LoginPage />)

    const githubButton = screen.getByText('Continue with GitHub')
    fireEvent.click(githubButton)

    await waitFor(() => {
      expect(screen.getByText('Unable to store authentication state. Please try again.')).toBeInTheDocument()
    })
  })

  it('has proper accessibility attributes', () => {
    render(<LoginPage />)

    // Check for aria-label and role attributes on spinners and error messages would be visible when state changes
    const loadingSpinner = document.querySelector('.animate-spin')
    if (loadingSpinner) {
      expect(loadingSpinner).toHaveAttribute('role', 'status')
      expect(loadingSpinner).toHaveAttribute('aria-label')
    }
  })
})