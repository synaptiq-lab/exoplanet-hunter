'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { 
  Upload, 
  Settings, 
  BarChart3, 
  Database, 
  ArrowRight,
  TrendingUp,
  Users,
  Clock,
  CheckCircle
} from 'lucide-react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { apiClient } from '@/lib/api';
import { ModelStats } from '@/types';
import { formatPercentage } from '@/lib/utils';

const DashboardHome = () => {
  const [modelStats, setModelStats] = useState<ModelStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadModelStats();
  }, []);

  const loadModelStats = async () => {
    try {
      const stats = await apiClient.getModelStats();
      setModelStats(stats);
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
    } finally {
      setLoading(false);
    }
  };

  const tools = [
    {
      id: 'datasets',
      title: 'Gestion des Datasets',
      description: 'Téléversez, analysez et entraînez vos modèles sur vos datasets d\'exoplanètes en un seul endroit',
      icon: Database,
      href: '/dashboard/datasets',
      color: 'from-blue-500 to-purple-500',
      stats: 'Tout-en-un'
    },
    {
      id: 'stats',
      title: 'Statistiques du Modèle',
      description: 'Consultez les métriques de performance et l\'évolution des modèles IA',
      icon: BarChart3,
      href: '/dashboard/stats',
      color: 'from-green-500 to-teal-500',
      stats: modelStats ? `${formatPercentage(modelStats.accuracy)} précision` : 'Chargement...'
    }
  ];

  const quickStats = [
    {
      label: 'Analyses Effectuées',
      value: '1,247',
      icon: TrendingUp,
      color: 'text-blue-400'
    },
    {
      label: 'Utilisateurs Actifs',
      value: '89',
      icon: Users,
      color: 'text-green-400'
    },
    {
      label: 'Temps Moyen',
      value: '2.3s',
      icon: Clock,
      color: 'text-yellow-400'
    },
    {
      label: 'Taux de Succès',
      value: '96.8%',
      icon: CheckCircle,
      color: 'text-purple-400'
    }
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Welcome Section */}
        <motion.div
          className="bg-gradient-to-r from-primary-900/20 to-purple-900/20 rounded-2xl p-8 border border-primary-500/20"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between">
            <div className="mb-6 lg:mb-0">
              <h1 className="text-3xl font-bold text-white mb-2">
                Bienvenue dans Exoplanet Hunter
              </h1>
              <p className="text-xl text-space-300 mb-4">
                Votre plateforme d'analyse et de découverte d'exoplanètes par IA
              </p>
              <p className="text-space-400 max-w-2xl">
                Utilisez les outils ci-dessous pour analyser vos données astronomiques, 
                entraîner des modèles personnalisés et explorer les datasets des missions NASA.
              </p>
            </div>
            
            <div className="flex flex-col items-end">
              <div className="text-right mb-2">
                <div className="text-2xl font-bold text-primary-400">
                  {modelStats ? formatPercentage(modelStats.accuracy) : '...'}
                </div>
                <div className="text-sm text-space-400">Précision du Modèle</div>
              </div>
              <div className="flex items-center space-x-2 text-green-400 text-sm">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span>Système Opérationnel</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickStats.map((stat, index) => (
            <motion.div
              key={index}
              className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{ scale: 1.02, y: -2 }}
            >
              <div className="flex items-center justify-between mb-4">
                <stat.icon className={`h-8 w-8 ${stat.color}`} />
                <div className="text-2xl font-bold text-white">{stat.value}</div>
              </div>
              <div className="text-space-400 text-sm">{stat.label}</div>
            </motion.div>
          ))}
        </div>

        {/* Tools Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {tools.map((tool, index) => (
            <motion.div
              key={tool.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <Link href={tool.href}>
                <div className="group bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-2xl p-8 hover:border-primary-500/50 transition-all duration-300 cursor-pointer h-full">
                  <div className="flex items-start justify-between mb-6">
                    <div className={`p-4 rounded-xl bg-gradient-to-br ${tool.color} shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                      <tool.icon className="h-8 w-8 text-white" />
                    </div>
                    <ArrowRight className="h-6 w-6 text-space-500 group-hover:text-primary-400 group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                  
                  <h3 className="text-2xl font-bold text-white mb-3 group-hover:text-primary-400 transition-colors">
                    {tool.title}
                  </h3>
                  
                  <p className="text-space-300 mb-4 leading-relaxed">
                    {tool.description}
                  </p>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-space-500">{tool.stats}</span>
                    <div className="flex items-center space-x-2 text-primary-400 font-medium group-hover:text-primary-300">
                      <span>Commencer</span>
                      <ArrowRight className="h-4 w-4" />
                    </div>
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>

        {/* Recent Activity */}
        <motion.div
          className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-2xl p-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <h2 className="text-2xl font-bold text-white mb-6">Activité Récente</h2>
          
          <div className="space-y-4">
            {[
              { action: 'Analyse de données', file: 'kepler_data_2024.csv', time: 'Il y a 2 minutes', status: 'success' },
              { action: 'Entraînement de modèle', file: 'custom_training_set.csv', time: 'Il y a 15 minutes', status: 'processing' },
              { action: 'Exploration de dataset', file: 'tess_observations.csv', time: 'Il y a 1 heure', status: 'completed' }
            ].map((activity, index) => (
              <motion.div
                key={index}
                className="flex items-center justify-between p-4 bg-space-700/30 rounded-lg border border-space-600"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="flex items-center space-x-4">
                  <div className={`w-3 h-3 rounded-full ${
                    activity.status === 'success' ? 'bg-green-400' :
                    activity.status === 'processing' ? 'bg-yellow-400 animate-pulse' :
                    'bg-blue-400'
                  }`}></div>
                  <div>
                    <div className="text-white font-medium">{activity.action}</div>
                    <div className="text-space-400 text-sm">{activity.file}</div>
                  </div>
                </div>
                <div className="text-space-500 text-sm">{activity.time}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </DashboardLayout>
  );
};

export default DashboardHome;
