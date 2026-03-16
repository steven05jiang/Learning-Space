'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
}

export default function NewResourcePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('auth_token');
    const userInfo = localStorage.getItem('user_info');

    if (!token || !userInfo) {
      router.push('/login');
      return;
    }

    try {
      setUser(JSON.parse(userInfo));
    } catch (e) {
      console.error('Failed to parse user info:', e);
      localStorage.removeItem('user_info');
      localStorage.removeItem('auth_token');
      router.push('/login');
      return;
    }

    setIsLoading(false);
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsSubmitting(true);

    try {
      // Validate URL
      if (!url.trim()) {
        throw new Error('URL is required');
      }

      // Basic URL validation
      try {
        new URL(url.trim());
      } catch {
        throw new Error('Please enter a valid URL');
      }

      // Get auth token
      const token = localStorage.getItem('auth_token');
      if (!token) {
        router.push('/login');
        return;
      }

      // Prepare request data
      const requestData = {
        content_type: 'url',
        original_content: url.trim(),
      };

      // Call the API
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseUrl}/resources/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user_info');
          router.push('/login');
          return;
        }

        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Error: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      setSuccess('Resource submitted successfully! It will be processed in the background.');

      // Clear form
      setUrl('');

      // Redirect to dashboard after a brief success message
      setTimeout(() => {
        router.push('/dashboard');
      }, 2000);

    } catch (err) {
      console.error('Error submitting resource:', err);
      setError(err instanceof Error ? err.message : 'Failed to submit resource');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    router.push('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" role="status" aria-label="Loading"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-gray-900">Learning Space</h1>
            </div>
            <div className="flex items-center space-x-4">
              <nav className="flex space-x-4">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Dashboard
                </button>
                <button
                  onClick={() => router.push('/resources/new')}
                  className="bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium"
                >
                  Add Resource
                </button>
              </nav>
              <div className="text-sm">
                <p className="font-medium text-gray-900">{user?.display_name}</p>
                <p className="text-gray-500">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="max-w-md mx-auto bg-white rounded-lg shadow">
            <div className="px-6 py-8">
              <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-gray-900">
                  Add New Resource
                </h2>
                <p className="mt-2 text-gray-600">
                  Submit a URL to add it to your learning resources
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label htmlFor="url" className="block text-sm font-medium text-gray-700">
                    URL *
                  </label>
                  <div className="mt-1">
                    <input
                      id="url"
                      name="url"
                      type="url"
                      required
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://example.com/article"
                      className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      disabled={isSubmitting}
                    />
                  </div>
                </div>


                {error && (
                  <div className="rounded-md bg-red-50 p-4">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <svg
                          className="h-5 w-5 text-red-400"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-red-800">{error}</p>
                      </div>
                    </div>
                  </div>
                )}

                {success && (
                  <div className="rounded-md bg-green-50 p-4">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <svg
                          className="h-5 w-5 text-green-400"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-green-800">{success}</p>
                      </div>
                    </div>
                  </div>
                )}

                <div>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isSubmitting ? (
                      <div className="flex items-center">
                        <svg
                          className="animate-spin h-5 w-5 mr-2"
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
                        Submitting...
                      </div>
                    ) : (
                      'Add Resource'
                    )}
                  </button>
                </div>
              </form>

              <div className="mt-6 text-center">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="text-sm text-blue-600 hover:text-blue-500"
                >
                  Back to Dashboard
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}