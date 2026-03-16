'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

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
  const [isLoadingResources, setIsLoadingResources] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({ total: 0, limit: 20, offset: 0 });

  // Auth check - same pattern as dashboard
  useEffect(() => {
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

  // Fetch resources from API
  const fetchResources = useCallback(async (customPagination?: { limit: number; offset: number }) => {
    if (!user) return;

    const token = localStorage.getItem('auth_token');
    if (!token) return;

    setIsLoadingResources(true);
    setError(null);

    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

    // Use custom pagination or default values
    const currentLimit = customPagination?.limit ?? 20;
    const currentOffset = customPagination?.offset ?? 0;

    try {
      const response = await fetch(
        `${apiBase}/resources?limit=${currentLimit}&offset=${currentOffset}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.status === 401) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
        router.push('/login');
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch resources: ${response.statusText}`);
      }

      const data: ResourceListResponse = await response.json();
      setResources(data.items);
      setPagination({ total: data.total, limit: data.limit, offset: data.offset });
    } catch (err) {
      console.error('Error fetching resources:', err);
      setError(err instanceof Error ? err.message : 'Failed to load resources');
    } finally {
      setIsLoadingResources(false);
    }
  }, [user, router]);

  // Load resources when user is set
  useEffect(() => {
    if (user) {
      fetchResources(pagination);
    }
  }, [user, fetchResources, pagination]);

  // Polling for status updates - every 10 seconds
  useEffect(() => {
    if (!user) return;

    const interval = setInterval(() => {
      fetchResources();
    }, 10000);

    return () => clearInterval(interval);
  }, [user, fetchResources]);

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    router.push('/login');
  };

  const getStatusBadgeColor = (status: Resource['status']) => {
    switch (status) {
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-800';
      case 'PROCESSING':
        return 'bg-blue-100 text-blue-800';
      case 'READY':
        return 'bg-green-100 text-green-800';
      case 'FAILED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSafeUrl = (url: string): string | undefined => {
    try {
      const parsed = new URL(url);
      return ['http:', 'https:'].includes(parsed.protocol) ? url : undefined;
    } catch {
      return undefined;
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" role="status" aria-label="Loading resources"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-8">
              <h1 className="text-3xl font-bold text-gray-900">Learning Space</h1>
              <nav className="flex space-x-4">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Dashboard
                </button>
                <span className="text-blue-600 px-3 py-2 rounded-md text-sm font-medium">
                  Resources
                </span>
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              {user?.avatar_url && (
                <Image
                  className="h-8 w-8 rounded-full"
                  src={user.avatar_url}
                  alt={user.display_name}
                  width={32}
                  height={32}
                />
              )}
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
          {/* Page Header */}
          <div className="mb-8 sm:flex sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Your Resources</h2>
              <p className="mt-1 text-sm text-gray-600">
                Manage and track your submitted learning resources
              </p>
            </div>
            <div className="mt-4 sm:mt-0">
              <button
                onClick={() => router.push('/resources/new')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Add New Resource
              </button>
            </div>
          </div>

          {/* Error State */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Loading Resources */}
          {isLoadingResources ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" role="status" aria-label="Loading resources"></div>
              <span className="ml-2 text-gray-600">Loading resources...</span>
            </div>
          ) : (
            <>
              {/* Empty State */}
              {resources.length === 0 ? (
                <div className="text-center py-12">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No resources yet</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Get started by submitting your first learning resource.
                  </p>
                  <div className="mt-6">
                    <button
                      onClick={() => router.push('/resources/new')}
                      className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <svg className="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      Add Resource
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  {/* Resource List */}
                  <div className="bg-white shadow overflow-hidden sm:rounded-md">
                    <ul className="divide-y divide-gray-200">
                      {resources.map((resource) => (
                        <li key={resource.id} className="px-6 py-4">
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center">
                                <div className="flex-1">
                                  <div className="flex items-center">
                                    <p className="text-sm font-medium text-gray-900 truncate">
                                      {resource.url && getSafeUrl(resource.url) ? (
                                        <a
                                          href={getSafeUrl(resource.url)}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="text-gray-900 hover:text-blue-600"
                                        >
                                          {resource.title || resource.url || 'Untitled Resource'}
                                        </a>
                                      ) : (
                                        resource.title || resource.url || 'Untitled Resource'
                                      )}
                                    </p>
                                    <span
                                      className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(
                                        resource.status
                                      )}`}
                                    >
                                      {resource.status}
                                    </span>
                                  </div>
                                  {resource.url && resource.title && (
                                    <p className="mt-1 text-sm text-gray-500 truncate">
                                      {getSafeUrl(resource.url) ? (
                                        <a
                                          href={getSafeUrl(resource.url)}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="text-blue-600 hover:text-blue-800"
                                        >
                                          {resource.url}
                                        </a>
                                      ) : (
                                        resource.url
                                      )}
                                    </p>
                                  )}
                                  {resource.status === 'READY' && resource.summary && (
                                    <p className="mt-2 text-sm text-gray-700 line-clamp-2">
                                      {resource.summary}
                                    </p>
                                  )}
                                  {resource.status === 'READY' && resource.tags.length > 0 && (
                                    <div className="mt-2 flex flex-wrap gap-1">
                                      {resource.tags.map((tag, index) => (
                                        <span
                                          key={index}
                                          className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800"
                                        >
                                          {tag}
                                        </span>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className="ml-6 flex-shrink-0">
                              <p className="text-sm text-gray-500">
                                {formatDate(resource.created_at)}
                              </p>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Pagination Info */}
                  <div className="mt-6 flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-700">
                        Showing <span className="font-medium">{pagination.offset + 1}</span> to{' '}
                        <span className="font-medium">
                          {Math.min(pagination.offset + pagination.limit, pagination.total)}
                        </span>{' '}
                        of <span className="font-medium">{pagination.total}</span> resources
                      </p>
                    </div>
                    {/* TODO: Add pagination controls when needed */}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}