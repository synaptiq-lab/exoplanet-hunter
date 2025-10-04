'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function DashboardHome() {
  const router = useRouter();

  useEffect(() => {
    // Redirection automatique vers la page d'analyse
    router.push('/dashboard/analyze');
  }, [router]);

  return (
    <div className="min-h-screen bg-space-gradient flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="h-12 w-12 text-primary-400 animate-spin mx-auto mb-4" />
        <p className="text-space-300 text-lg">Chargement...</p>
      </div>
    </div>
  );
}
