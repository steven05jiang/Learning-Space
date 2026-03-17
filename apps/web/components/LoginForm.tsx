'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useMock } from '@/lib/mock/hooks';

export function LoginForm() {
  const router = useRouter();
  const isMock = useMock();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (isMock) {
      // Mock mode: skip API, go straight to dashboard
      await new Promise((r) => setTimeout(r, 600));
      router.push('/dashboard');
      return;
    }

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const res = await fetch(`${apiBase}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) throw new Error('Invalid credentials');
      const data = await res.json();
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('user_info', JSON.stringify(data.user));
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed');
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError('');
    setIsGoogleLoading(true);

    if (isMock) {
      await new Promise((r) => setTimeout(r, 600));
      router.push('/dashboard');
      return;
    }

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const res = await fetch(`${apiBase}/auth/login/google`);
      if (!res.ok) throw new Error('Failed to initiate Google login');
      const data = await res.json();
      if (data.authorization_url) {
        if (data.state) localStorage.setItem('oauth_state_google', data.state);
        window.location.href = data.authorization_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Google login failed');
      setIsGoogleLoading(false);
    }
  };

  return (
    <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-md p-8 w-full max-w-sm dark:bg-slate-900/80">
      {/* Logo */}
      <div className="flex flex-col items-center gap-2 mb-8">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-500 text-white">
          <BookOpen size={20} />
        </div>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Learning Space</h1>
        <p className="text-sm text-gray-500 dark:text-slate-400">Sign in to your account</p>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-600 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Mock badge */}
      {isMock && (
        <div className="mb-4 px-4 py-2 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-700 text-center dark:bg-amber-900/20 dark:border-amber-800 dark:text-amber-400">
          Mock mode — any credentials will work
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSignIn} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="email">
            Email
          </label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required={!isMock}
            className="rounded-xl border-gray-200 dark:border-slate-700 dark:bg-slate-800 dark:text-gray-100"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="password">
            Password
          </label>
          <Input
            id="password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required={!isMock}
            className="rounded-xl border-gray-200 dark:border-slate-700 dark:bg-slate-800 dark:text-gray-100"
          />
        </div>

        <Button
          type="submit"
          disabled={isLoading}
          className="w-full rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white font-medium transition-colors"
        >
          {isLoading ? <Loader2 size={16} className="animate-spin mr-2" /> : null}
          Sign In
        </Button>
      </form>

      {/* Forgot password */}
      <div className="mt-3 text-center">
        <button className="text-sm text-indigo-500 hover:text-indigo-600 transition-colors dark:text-indigo-400">
          Forgot password?
        </button>
      </div>

      {/* Divider */}
      <div className="my-6 flex items-center gap-3">
        <div className="flex-1 h-px bg-gray-200 dark:bg-slate-700" />
        <span className="text-xs text-gray-400 dark:text-slate-500">or</span>
        <div className="flex-1 h-px bg-gray-200 dark:bg-slate-700" />
      </div>

      {/* Google */}
      <Button
        type="button"
        variant="outline"
        onClick={handleGoogleLogin}
        disabled={isGoogleLoading}
        className="w-full rounded-lg border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors dark:border-slate-700 dark:text-gray-300 dark:hover:bg-slate-800"
      >
        {isGoogleLoading ? (
          <Loader2 size={16} className="animate-spin mr-2" />
        ) : (
          <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
        )}
        Continue with Google
      </Button>
    </div>
  );
}
