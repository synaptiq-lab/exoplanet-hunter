'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  BarChart3, 
  Upload, 
  Settings, 
  Database, 
  Home,
  Rocket
} from 'lucide-react';

interface SidebarProps {}

const Sidebar: React.FC<SidebarProps> = () => {
  const pathname = usePathname();

  const menuItems = [
    {
      id: 'analyze',
      label: 'Analyser',
      icon: Upload,
      href: '/dashboard/analyze',
      description: 'Détecter des exoplanètes'
    }
  ];

  return (
    <div className="fixed left-0 top-0 h-full w-64 bg-space-800/95 backdrop-blur-md border-r border-space-700 z-50">
      {/* Header */}
      <div className="flex items-center justify-center p-4 border-b border-space-700">
        <div className="flex items-center space-x-3">
          <Rocket className="h-8 w-8 text-primary-400" />
          <div>
            <h1 className="text-lg font-bold gradient-text">Exoplanet Hunter</h1>
            <p className="text-xs text-space-400">Dashboard</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-2">
        {menuItems.map((item) => {
          const isActive = pathname === item.href;
          
          return (
            <Link key={item.id} href={item.href}>
              <motion.div
                className={`flex items-center space-x-3 p-3 rounded-lg transition-all duration-200 group cursor-pointer ${
                  isActive
                    ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/25'
                    : 'text-space-300 hover:bg-space-700 hover:text-white'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <item.icon className={`h-5 w-5 ${isActive ? 'text-white' : 'text-space-400 group-hover:text-primary-400'}`} />
                
                <div className="flex-1">
                  <div className="font-medium">{item.label}</div>
                  <div className={`text-xs ${isActive ? 'text-primary-100' : 'text-space-500'}`}>
                    {item.description}
                  </div>
                </div>
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-space-700">
        <div className="text-center">
          <p className="text-xs text-space-500 mb-2">
            NASA Space Apps Challenge 2024
          </p>
          <Link href="/">
            <motion.button
              className="text-xs text-primary-400 hover:text-primary-300 transition-colors"
              whileHover={{ scale: 1.05 }}
            >
              ← Retour à l'accueil
            </motion.button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  BarChart3, 
  Upload, 
  Settings, 
  Database, 
  Home,
  Rocket,
  Cpu,
  Satellite
} from 'lucide-react';

interface SidebarProps {}

const Sidebar: React.FC<SidebarProps> = () => {
  const pathname = usePathname();

  const menuItems = [
    {
      id: 'analyze',
      label: 'Analyser',
      icon: Upload,
      href: '/dashboard/analyze',
      description: 'Détecter des exoplanètes'
    },
    {
      id: 'exominer',
      label: 'ExoMiner',
      icon: Satellite,
      href: '/dashboard/exominer',
      description: 'Analyse NASA ExoMiner'
    },
    {
      id: 'models',
      label: 'Mes Modèles',
      icon: Cpu,
      href: '/dashboard/models',
      description: 'Gérer mes modèles'
    }
  ];

  return (
    <div className="fixed left-0 top-0 h-full w-64 bg-space-800/95 backdrop-blur-md border-r border-space-700 z-50">
      {/* Header */}
      <div className="flex items-center justify-center p-4 border-b border-space-700">
        <div className="flex items-center space-x-3">
          <Rocket className="h-8 w-8 text-primary-400" />
          <div>
            <h1 className="text-lg font-bold gradient-text">Exoplanet Hunter</h1>
            <p className="text-xs text-space-400">Dashboard</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-2">
        {menuItems.map((item) => {
          const isActive = pathname === item.href;
          
          return (
            <Link key={item.id} href={item.href}>
              <motion.div
                className={`flex items-center space-x-3 p-3 rounded-lg transition-all duration-200 group cursor-pointer ${
                  isActive
                    ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/25'
                    : 'text-space-300 hover:bg-space-700 hover:text-white'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <item.icon className={`h-5 w-5 ${isActive ? 'text-white' : 'text-space-400 group-hover:text-primary-400'}`} />
                
                <div className="flex-1">
                  <div className="font-medium">{item.label}</div>
                  <div className={`text-xs ${isActive ? 'text-primary-100' : 'text-space-500'}`}>
                    {item.description}
                  </div>
                </div>
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-space-700">
        <div className="text-center">
          <p className="text-xs text-space-500 mb-2">
            NASA Space Apps Challenge 2024
          </p>
          <Link href="/">
            <motion.button
              className="text-xs text-primary-400 hover:text-primary-300 transition-colors"
              whileHover={{ scale: 1.05 }}
            >
              ← Retour à l'accueil
            </motion.button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
