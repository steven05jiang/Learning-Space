'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
}

interface CallbackResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export default function OAuthCallbackPage({
  params,
}: {
  params: { provider: string };
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code');
        const state = searchParams.get('state');

        if (!code) {
          throw new Error('Authorization code not received');
        }

        // Call the backend callback endpoint
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        const url = new URL(`${apiBaseUrl}/auth/callback/${params.provider}`);
        url.searchParams.set('code', code);
        if (state) {
          url.searchParams.set('state', state);
        }

        const response = await fetch(url.toString());

        if (!response.ok) {
          const errorData = await response.json().catch(() => null);
          throw new Error(errorData?.detail || 'Authentication failed');
        }

        const data: CallbackResponse = await response.json();

        if (data.access_token && data.user) {
          // Store the JWT token and user info
          localStorage.setItem('auth_token', data.access_token);
          localStorage.setItem('user_info', JSON.stringify(data.user));

          setStatus('success');

          // Redirect to dashboard or home after a brief success message
          setTimeout(() => {
            router.push('/dashboard');
          }, 1500);
        } else {
          throw new Error('Invalid response from authentication server');
        }
      } catch (err) {
        console.error('OAuth callback error:', err);
        setError(err instanceof Error ? err.message : 'Authentication failed');
        setStatus('error');

        // Redirect to login page after showing error
        setTimeout(() => {
          router.push('/login?error=auth_failed');
        }, 3000);
      }
    };

    handleCallback();
  }, [params.provider, searchParams, router]);

  const providerDisplayName = params.provider.charAt(0).toUpperCase() + params.provider.slice(1);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {status === 'loading' && (
            <div className="text-center">
              <div className="flex justify-center">
                <svg
                  className="animate-spin h-12 w-12 text-blue-600"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
              </div>
              <h2 className="mt-4 text-lg font-semibold text-gray-900">
                Completing {providerDisplayName} login...
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Please wait while we authenticate your account.
              </p>
            </div>
          )}

          {status === 'success' && (
            <div className="text-center">
              <div className="flex justify-center">
                <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                  <svg
                    className="h-6 w-6 text-green-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
              </div>
              <h2 className="mt-4 text-lg font-semibold text-gray-900">
                Login successful!
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Redirecting you to your dashboard...
              </p>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center">
              <div className="flex justify-center">
                <div className="h-12 w-12 bg-red-100 rounded-full flex items-center justify-center">
                  <svg
                    className="h-6 w-6 text-red-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </div>
              </div>
              <h2 className="mt-4 text-lg font-semibold text-gray-900">
                Authentication failed
              </h2>
              <p className="mt-2 text-sm text-gray-600">{error}</p>
              <p className="mt-2 text-xs text-gray-500">
                Redirecting to login page...
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}