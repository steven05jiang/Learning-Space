'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in - consistent auth check with login page
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

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    router.push('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" role="status" aria-label="Loading dashboard"></div>
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
                  className="bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium"
                >
                  Dashboard
                </button>
                <button
                  onClick={() => router.push('/resources')}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium transition-colors"
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
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Welcome to Learning Space!
            </h2>
            <p className="text-gray-600 mb-6">
              You have successfully logged in with OAuth. Start building your learning collection by adding resources.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Add Resource Card */}
            <div
              onClick={() => router.push('/resources/new')}
              className="bg-white rounded-lg shadow hover:shadow-lg cursor-pointer transition-shadow border-2 border-dashed border-gray-200 hover:border-blue-300"
            >
              <div className="p-6 text-center">
                <div className="text-4xl mb-4">➕</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Add New Resource
                </h3>
                <p className="text-gray-600 text-sm">
                  Submit a URL to start learning from web content
                </p>
              </div>
            </div>

            {/* View Resources Card */}
            <div
              onClick={() => router.push('/resources')}
              className="bg-white rounded-lg shadow hover:shadow-lg cursor-pointer transition-shadow"
            >
              <div className="p-6 text-center">
                <div className="text-4xl mb-4">📚</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  View Resources
                </h3>
                <p className="text-gray-600 text-sm">
                  Browse your learning collection and track progress
                </p>
              </div>
            </div>

            {/* Coming Soon Card */}
            <div className="bg-white rounded-lg shadow border-2 border-gray-100">
              <div className="p-6 text-center">
                <div className="text-4xl mb-4">🚀</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Analytics
                </h3>
                <p className="text-gray-600 text-sm">
                  Track your learning progress and insights
                </p>
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500 mt-2">
                  Coming Soon
                </span>
              </div>
            </div>
          </div>

          <div className="mt-8 bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-green-400"
                  width="20"
                  height="20"
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
                <p className="text-sm text-green-800">
                  Authentication successful! Your session is now active.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}