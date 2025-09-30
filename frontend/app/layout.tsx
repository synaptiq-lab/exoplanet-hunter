import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Exoplanet Hunter - Détection IA d\'Exoplanètes',
  description: 'Application de détection d\'exoplanètes utilisant l\'intelligence artificielle et les données ouvertes des missions spatiales NASA.',
  keywords: 'exoplanètes, NASA, intelligence artificielle, machine learning, Kepler, TESS, K2',
  authors: [{ name: 'Exoplanet Hunter Team' }],
  openGraph: {
    title: 'Exoplanet Hunter - Détection IA d\'Exoplanètes',
    description: 'Découvrez des exoplanètes avec l\'IA',
    type: 'website',
  },
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#3b82f6',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="scroll-smooth">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}

