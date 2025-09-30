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
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggle }) => {
  const pathname = usePathname();

  const menuItems = [
    {
      id: 'dashboard',
      label: 'Tableau de Bord',
      icon: Home,
      href: '/dashboard',
      description: 'Vue d\'ensemble et statistiques'
    },
    {
      id: 'datasets',
      label: 'Datasets',
      icon: Database,
      href: '/dashboard/datasets',
      description: 'Gestion complète des datasets'
    }
  ];

  return (
    <motion.div
      className={`fixed left-0 top-0 h-full bg-space-800/95 backdrop-blur-md border-r border-space-700 z-50 transition-all duration-300 ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
      initial={false}
      animate={{ width: isCollapsed ? 64 : 256 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-space-700">
        {!isCollapsed && (
          <motion.div
            className="flex items-center space-x-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Rocket className="h-8 w-8 text-primary-400" />
            <div>
              <h1 className="text-lg font-bold gradient-text">Exoplanet Hunter</h1>
              <p className="text-xs text-space-400">Dashboard</p>
            </div>
          </motion.div>
        )}
        
        <motion.button
          onClick={onToggle}
          className="p-2 rounded-lg bg-space-700 hover:bg-space-600 text-space-300 hover:text-white transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </motion.button>
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
                
                {!isCollapsed && (
                  <motion.div
                    className="flex-1"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                  >
                    <div className="font-medium">{item.label}</div>
                    <div className={`text-xs ${isActive ? 'text-primary-100' : 'text-space-500'}`}>
                      {item.description}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-space-700">
        {!isCollapsed && (
          <motion.div
            className="text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
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
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default Sidebar;
