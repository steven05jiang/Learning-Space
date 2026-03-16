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

beforeEach(() => {
  ;(useRouter as jest.Mock).mockReturnValue({
    push: mockPush,
  })
  ;(useSearchParams as jest.Mock).mockReturnValue({
    get: mockGet,
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

    render(<LoginPage />)

    expect(mockPush).toHaveBeenCalledWith('/')
  })

  it('redirects to returnTo URL if provided', () => {
    localStorage.setItem('auth_token', 'mock-token')
    mockGet.mockReturnValue('/dashboard')

    render(<LoginPage />)

    expect(mockPush).toHaveBeenCalledWith('/dashboard')
  })

  it('initiates OAuth login when provider button is clicked', async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        authorization_url: 'https://github.com/login/oauth/authorize?test',
        provider: 'github',
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
    // (the redirect would happen in a real browser)
    expect(mockResponse.json).toHaveBeenCalled()
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
})