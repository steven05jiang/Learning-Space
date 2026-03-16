'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
}

interface Resource {
  id: string;
  url?: string;
  title?: string;
  summary?: string;
  tags: string[];
  status: 'PENDING' | 'PROCESSING' | 'READY' | 'FAILED';
  created_at: string;
}

interface ResourceListResponse {
  items: Resource[];
  total: number;
  limit: number;
  offset: number;
}

export default function ResourcesPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [resources, setResources] = useState<Resource[]>([]);
  const [isLoadingResources, setIsLoadingResources] = useState(false);
  const [error, setError] = useState('');

  const loadResources = useCallback(async () => {
    setIsLoadingResources(true);
    setError('');

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseUrl}/resources/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user_info');
          router.push('/login');
          return;
        }

        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Error: ${response.status} ${response.statusText}`);
      }

      const data: ResourceListResponse = await response.json();
      setResources(data.items);
    } catch (err) {
      console.error('Error loading resources:', err);
      setError(err instanceof Error ? err.message : 'Failed to load resources');
    } finally {
      setIsLoadingResources(false);
    }
  }, [router]);

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
    loadResources();
  }, [router, loadResources]);

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    router.push('/login');
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'READY':
        return 'bg-green-100 text-green-800';
      case 'PROCESSING':
        return 'bg-blue-100 text-blue-800';
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-800';
      case 'FAILED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
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
                  onClick={() => router.push('/resources')}
                  className="bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium"
                >
                  Resources
                </button>
                <button
                  onClick={() => router.push('/resources/new')}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium transition-colors"
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
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Your Resources</h2>
            <button
              onClick={() => router.push('/resources/new')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Add New Resource
            </button>
          </div>

          {error && (
            <div className="mb-6 rounded-md bg-red-50 p-4">
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
                  <button
                    onClick={loadResources}
                    className="mt-2 text-sm text-red-600 hover:text-red-500 underline"
                  >
                    Try again
                  </button>
                </div>
              </div>
            </div>
          )}

          {isLoadingResources ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading resources...</p>
            </div>
          ) : resources.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📚</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No resources yet
              </h3>
              <p className="text-gray-600 mb-4">
                Start building your learning collection by adding your first resource.
              </p>
              <button
                onClick={() => router.push('/resources/new')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Add Your First Resource
              </button>
            </div>
          ) : (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {resources.map((resource) => (
                  <li key={resource.id}>
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-blue-600 truncate">
                              {resource.title || resource.url || 'Untitled Resource'}
                            </p>
                            <div className="ml-2 flex-shrink-0 flex">
                              <span
                                className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeColor(
                                  resource.status
                                )}`}
                              >
                                {resource.status}
                              </span>
                            </div>
                          </div>
                          {resource.url && (
                            <p className="mt-1 text-sm text-gray-600 truncate">
                              {resource.url}
                            </p>
                          )}
                          {resource.summary && (
                            <p className="mt-1 text-sm text-gray-600">
                              {resource.summary}
                            </p>
                          )}
                          {resource.tags.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {resource.tags.map((tag, index) => (
                                <span
                                  key={index}
                                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="mt-2 sm:flex sm:justify-between">
                        <div className="sm:flex">
                          <p className="text-sm text-gray-500">
                            Added {formatDate(resource.created_at)}
                          </p>
                        </div>
                        {resource.url && (
                          <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                            <a
                              href={resource.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-500"
                            >
                              View Original
                            </a>
                          </div>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}