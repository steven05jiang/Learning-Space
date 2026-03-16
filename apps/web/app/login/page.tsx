'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

interface Provider {
  name: string;
  displayName: string;
  icon: string;
  bgColor: string;
  textColor: string;
}

const PROVIDERS: Provider[] = [
  {
    name: 'github',
    displayName: 'GitHub',
    icon: '🐙',
    bgColor: 'bg-gray-900 hover:bg-gray-800',
    textColor: 'text-white',
  },
  {
    name: 'google',
    displayName: 'Google',
    icon: '🔍',
    bgColor: 'bg-blue-600 hover:bg-blue-700',
    textColor: 'text-white',
  },
  {
    name: 'twitter',
    displayName: 'Twitter',
    icon: '🐦',
    bgColor: 'bg-sky-500 hover:bg-sky-600',
    textColor: 'text-white',
  },
];

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('auth_token');
    if (token) {
      // Redirect to dashboard or home based on search params
      const returnTo = searchParams.get('returnTo') || '/';
      router.push(returnTo);
    }
  }, [router, searchParams]);

  const handleOAuthLogin = async (provider: string) => {
    try {
      setIsLoading(provider);
      setError('');

      // Get the authorization URL from the backend
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseUrl}/auth/login/${provider}`);

      if (!response.ok) {
        throw new Error(`Failed to initiate ${provider} login`);
      }

      const data = await response.json();

      if (data.authorization_url) {
        // Redirect to the OAuth provider
        window.location.href = data.authorization_url;
      } else {
        throw new Error('No authorization URL received');
      }
    } catch (err) {
      console.error(`OAuth login error for ${provider}:`, err);
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.');
      setIsLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Learning Space</h1>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Choose your preferred login method
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            {PROVIDERS.map((provider) => (
              <button
                key={provider.name}
                onClick={() => handleOAuthLogin(provider.name)}
                disabled={!!isLoading}
                className={`w-full flex justify-center items-center px-4 py-3 border border-transparent rounded-md shadow-sm text-sm font-medium transition-colors duration-200 ${
                  provider.bgColor
                } ${provider.textColor} ${
                  isLoading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <span className="mr-3 text-lg">{provider.icon}</span>
                {isLoading === provider.name ? (
                  <>
                    <svg
                      className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
                    Connecting...
                  </>
                ) : (
                  `Continue with ${provider.displayName}`
                )}
              </button>
            ))}
          </div>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">
                  Secure OAuth authentication
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}