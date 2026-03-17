'use client';

import { Suspense } from 'react';
import { LoginForm } from '@/components/LoginForm';

function LoginPageContent() {
  return (
    <div
      className="min-h-screen flex items-center justify-center p-4 dark:[background:linear-gradient(135deg,#312e81,#4c1d95,#831843)]"
      style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899)' }}
    >
      <LoginForm />
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div
          className="min-h-screen flex items-center justify-center"
          style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899)' }}
        >
          <div className="w-8 h-8 rounded-full border-2 border-white/40 border-t-white animate-spin" />
        </div>
      }
    >
      <LoginPageContent />
    </Suspense>
  );
}
