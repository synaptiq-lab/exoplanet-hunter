'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Rocket, Github, ExternalLink } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-space-gradient relative overflow-x-hidden">
      {/* Fond étoilé animé */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-10 left-10 w-1 h-1 bg-white rounded-full animate-pulse"></div>
          <div className="absolute top-20 right-20 w-1 h-1 bg-white rounded-full animate-pulse" style={{animationDelay: '1s'}}></div>
          <div className="absolute top-40 left-1/3 w-1 h-1 bg-white rounded-full animate-pulse" style={{animationDelay: '2s'}}></div>
          <div className="absolute top-60 right-1/3 w-1 h-1 bg-white rounded-full animate-pulse" style={{animationDelay: '0.5s'}}></div>
          <div className="absolute bottom-40 left-20 w-1 h-1 bg-white rounded-full animate-pulse" style={{animationDelay: '1.5s'}}></div>
          <div className="absolute bottom-20 right-10 w-1 h-1 bg-white rounded-full animate-pulse" style={{animationDelay: '2.5s'}}></div>
        </div>
        {/* Planètes flottantes */}
        <motion.div
          className="absolute top-20 left-10 w-4 h-4 bg-primary-500 rounded-full opacity-60"
          animate={{
            y: [0, -20, 0],
            x: [0, 10, 0],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute top-40 right-20 w-6 h-6 bg-yellow-400 rounded-full opacity-40"
          animate={{
            y: [0, 30, 0],
            x: [0, -15, 0],
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute bottom-40 left-1/4 w-3 h-3 bg-purple-400 rounded-full opacity-50"
          animate={{
            y: [0, -25, 0],
            x: [0, 20, 0],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </div>

      {/* Header */}
      <motion.header
        className="relative z-10 bg-space-800/30 backdrop-blur-md border-b border-space-700"
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8 }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <motion.div 
              className="flex items-center space-x-3"
              whileHover={{ scale: 1.05 }}
            >
              <Rocket className="h-8 w-8 text-primary-400" />
              <div>
                <h1 className="text-xl font-bold gradient-text">Exoplanet Hunter</h1>
                <p className="text-xs text-space-400">Détection IA d'exoplanètes</p>
              </div>
            </motion.div>
            
            <div className="hidden md:flex items-center space-x-4">
              <motion.a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-space-300 hover:text-white transition-colors"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                <Github className="h-5 w-5" />
                <span>GitHub</span>
              </motion.a>
              <motion.a
                href="https://exoplanetarchive.ipac.caltech.edu/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-space-300 hover:text-white transition-colors"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                <ExternalLink className="h-5 w-5" />
                <span>NASA Archive</span>
              </motion.a>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Contenu principal */}
      <main className="relative z-10 min-h-screen">
        {children}
      </main>

      {/* Footer */}
      <motion.footer
        className="relative z-10 bg-space-800/30 backdrop-blur-md border-t border-space-700 mt-20"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 0.5 }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">À propos</h3>
              <p className="text-space-400 text-sm">
                Application de détection d'exoplanètes utilisant l'intelligence artificielle 
                et les données ouvertes des missions spatiales NASA.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Missions</h3>
              <ul className="text-space-400 text-sm space-y-2">
                <li>• Kepler (2009-2017)</li>
                <li>• K2 (2014-2018)</li>
                <li>• TESS (2018-présent)</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Méthodes</h3>
              <ul className="text-space-400 text-sm space-y-2">
                <li>• Méthode du transit</li>
                <li>• Machine Learning</li>
                <li>• Analyse automatisée</li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-space-700 mt-8 pt-8 text-center">
            <p className="text-space-400 text-sm">
              © 2024 Exoplanet Hunter - Hackathon NASA Space Apps Challenge
            </p>
          </div>
        </div>
      </motion.footer>
    </div>
  );
};

export default Layout;
