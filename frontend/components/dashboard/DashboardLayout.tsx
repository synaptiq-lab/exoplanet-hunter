'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Sidebar from './Sidebar';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-space-gradient">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="ml-64">
        {/* Header Bar */}
        <div className="bg-space-800/30 backdrop-blur-md border-b border-space-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Dashboard</h1>
              <p className="text-space-400 text-sm">
                Outils d'analyse et d'entraînement pour la détection d'exoplanètes
              </p>
            </div>
            
           
          </div>
        </div>

        {/* Content Area */}
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;

