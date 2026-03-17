'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'

interface User {
  id: string
  email: string
  display_name: string
  avatar_url?: string
}

interface CallbackResponse {
  access_token: string
  token_type: string
  user: User
}

function OAuthCallbackContent({ params }: { params: { provider: string } }) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [error, setError] = useState<string>('')

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code')
        const state = searchParams.get('state')

        if (!code) throw new Error('Authorization code not received')
        if (!state) throw new Error('State parameter missing')

        const storedState = localStorage.getItem(`oauth_state_${params.provider}`)
        if (!storedState || storedState !== state) {
          throw new Error('Invalid state parameter - possible CSRF attack')
        }

        localStorage.removeItem(`oauth_state_${params.provider}`)

        const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
        const url = new URL(`${apiBase}/auth/callback/${params.provider}`)
        url.searchParams.set('code', code)
        url.searchParams.set('state', state)

        const response = await fetch(url.toString())

        if (!response.ok) {
          const errorData = await response.json().catch(() => null)
          throw new Error(errorData?.detail ?? 'Authentication failed')
        }

        const data: CallbackResponse = await response.json()

        if (data.access_token && data.user) {
          try {
            localStorage.setItem('auth_token', data.access_token)
            localStorage.setItem('user_info', JSON.stringify(data.user))
          } catch {
            localStorage.clear()
            try {
              localStorage.setItem('auth_token', data.access_token)
              localStorage.setItem('user_info', JSON.stringify(data.user))
            } catch {
              throw new Error('Unable to save login session. Please try again.')
            }
          }

          setStatus('success')
          setTimeout(() => router.push('/dashboard'), 1500)
        } else {
          throw new Error('Invalid response from authentication server')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Authentication failed')
        setStatus('error')
        localStorage.removeItem(`oauth_state_${params.provider}`)
        setTimeout(() => router.push('/login?error=auth_failed'), 3000)
      }
    }

    handleCallback()
  }, [params.provider, searchParams, router])

  const providerName =
    params.provider.charAt(0).toUpperCase() + params.provider.slice(1)

  return (
    <div className="flex min-h-svh items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm rounded-2xl border border-border bg-card p-8 shadow-sm text-center">
        {status === 'loading' && (
          <>
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-muted-foreground" />
            <h2 className="mt-4 text-lg font-semibold text-foreground">
              Completing {providerName} login…
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Please wait while we authenticate your account.
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
            <h2 className="mt-4 text-lg font-semibold text-foreground">Login successful!</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Redirecting you to your dashboard…
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <XCircle className="mx-auto h-12 w-12 text-destructive" />
            <h2 className="mt-4 text-lg font-semibold text-foreground">
              Authentication failed
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">{error}</p>
            <p className="mt-1 text-xs text-muted-foreground">Redirecting to login page…</p>
          </>
        )}
      </div>
    </div>
  )
}

export default function OAuthCallbackPage({
  params,
}: {
  params: { provider: string }
}) {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-svh items-center justify-center bg-background">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <OAuthCallbackContent params={params} />
    </Suspense>
  )
}
