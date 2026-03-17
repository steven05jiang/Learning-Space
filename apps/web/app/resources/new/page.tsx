'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { useMock } from '@/lib/mock/hooks'

interface User {
  id: string
  email: string
  display_name: string
  avatar_url?: string
}

export default function NewResourcePage() {
  const router = useRouter()
  const isMock = useMock()
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (isMock) {
      setUser({ id: 'mock', email: 'alex@learningspace.dev', display_name: 'Alex Chen' })
      setIsLoading(false)
      return
    }

    const token = localStorage.getItem('auth_token')
    const userInfo = localStorage.getItem('user_info')

    if (!token || !userInfo) {
      router.push('/login')
      return
    }

    try {
      setUser(JSON.parse(userInfo))
    } catch {
      localStorage.removeItem('user_info')
      localStorage.removeItem('auth_token')
      router.push('/login')
      return
    }

    setIsLoading(false)
  }, [router, isMock])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSubmitting(true)

    try {
      if (!url.trim()) throw new Error('URL is required')

      try {
        new URL(url.trim())
      } catch {
        throw new Error('Please enter a valid URL')
      }

      if (isMock) {
        await new Promise((r) => setTimeout(r, 800))
        setSuccess('Resource submitted successfully! It will be processed in the background.')
        setUrl('')
        setTimeout(() => router.push('/resources'), 2000)
        return
      }

      const token = localStorage.getItem('auth_token')
      if (!token) {
        router.push('/login')
        return
      }

      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
      const response = await fetch(`${apiBase}/resources/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ content_type: 'url', original_content: url.trim() }),
      })

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user_info')
          router.push('/login')
          return
        }
        const errorData = await response.json().catch(() => null)
        throw new Error(errorData?.detail ?? `Error: ${response.status} ${response.statusText}`)
      }

      setSuccess('Resource submitted successfully! It will be processed in the background.')
      setUrl('')
      setTimeout(() => router.push('/resources'), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit resource')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-56px)] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-foreground" />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        className="-ml-2 w-fit"
        onClick={() => router.push('/resources')}
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Resources
      </Button>

      <div className="mx-auto w-full max-w-lg">
        <Card>
          <CardHeader>
            <CardTitle>Add New Resource</CardTitle>
            <CardDescription>
              Submit a URL to add it to your learning resources. We&apos;ll process and summarize
              it for you.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="url">URL</Label>
                <Input
                  id="url"
                  type="url"
                  placeholder="https://example.com/article"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required
                  disabled={isSubmitting}
                  className="h-11"
                />
              </div>

              {error && (
                <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              {success && (
                <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400">
                  {success}
                </div>
              )}

              <Button
                type="submit"
                className="h-11 w-full"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Spinner className="mr-2 h-4 w-4" />
                    Submitting...
                  </>
                ) : (
                  'Add Resource'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
