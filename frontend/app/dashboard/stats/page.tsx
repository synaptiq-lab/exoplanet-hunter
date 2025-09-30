'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend
} from 'recharts';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { apiClient } from '@/lib/api';
import { ModelStats } from '@/types';
import { formatPercentage, formatDate } from '@/lib/utils';
import { TrendingUp, Target, Clock, Database } from 'lucide-react';

const StatsPage = () => {
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

  // Données simulées pour les graphiques
  const performanceHistory = [
    { date: '2024-01', accuracy: 0.87, precision: 0.84, recall: 0.89 },
    { date: '2024-02', accuracy: 0.89, precision: 0.86, recall: 0.91 },
    { date: '2024-03', accuracy: 0.91, precision: 0.88, recall: 0.93 },
    { date: '2024-04', accuracy: 0.92, precision: 0.89, recall: 0.94 },
  ];

  const classificationData = [
    { name: 'Confirmées', value: 2847, color: '#10b981' },
    { name: 'Candidates', value: 4521, color: '#f59e0b' },
    { name: 'Faux Positifs', value: 1632, color: '#ef4444' }
  ];

  const algorithmComparison = [
    { algorithm: 'Random Forest', accuracy: 0.92, speed: 95 },
    { algorithm: 'Neural Network', accuracy: 0.94, speed: 78 },
    { algorithm: 'SVM', accuracy: 0.88, speed: 82 },
    { algorithm: 'Gradient Boosting', accuracy: 0.93, speed: 71 }
  ];

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-3xl font-bold text-white mb-4">
            Statistiques et Performances
          </h1>
          <p className="text-space-300 text-lg">
            Analysez les performances des modèles et suivez l'évolution des métriques de classification.
          </p>
        </motion.div>

        {/* Key Metrics */}
        {modelStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                label: 'Précision',
                value: formatPercentage(modelStats.accuracy),
                icon: Target,
                color: 'text-green-400',
                bg: 'bg-green-500/10 border-green-500/30'
              },
              {
                label: 'Precision',
                value: formatPercentage(modelStats.precision),
                icon: TrendingUp,
                color: 'text-blue-400',
                bg: 'bg-blue-500/10 border-blue-500/30'
              },
              {
                label: 'Recall',
                value: formatPercentage(modelStats.recall),
                icon: Database,
                color: 'text-purple-400',
                bg: 'bg-purple-500/10 border-purple-500/30'
              },
              {
                label: 'F1-Score',
                value: formatPercentage(modelStats.f1_score),
                icon: Clock,
                color: 'text-yellow-400',
                bg: 'bg-yellow-500/10 border-yellow-500/30'
              }
            ].map((metric, index) => (
              <motion.div
                key={index}
                className={`p-6 rounded-xl border ${metric.bg}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{ scale: 1.02 }}
              >
                <div className="flex items-center justify-between mb-4">
                  <metric.icon className={`h-8 w-8 ${metric.color}`} />
                  <div className={`text-3xl font-bold ${metric.color}`}>
                    {metric.value}
                  </div>
                </div>
                <div className="text-space-400">{metric.label}</div>
              </motion.div>
            ))}
          </div>
        )}

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Performance History */}
          <motion.div
            className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h2 className="text-xl font-semibold text-white mb-6">
              Évolution des Performances
            </h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={performanceHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} domain={[0.8, 1]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #475569',
                      borderRadius: '8px',
                      color: '#ffffff'
                    }}
                    formatter={(value: any) => [formatPercentage(value), '']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="accuracy" 
                    stroke="#10b981" 
                    strokeWidth={3}
                    name="Précision"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="precision" 
                    stroke="#3b82f6" 
                    strokeWidth={3}
                    name="Precision"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="recall" 
                    stroke="#8b5cf6" 
                    strokeWidth={3}
                    name="Recall"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Classification Distribution */}
          <motion.div
            className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <h2 className="text-xl font-semibold text-white mb-6">
              Distribution des Classifications
            </h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={classificationData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {classificationData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #475569',
                      borderRadius: '8px',
                      color: '#ffffff'
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        </div>

        {/* Algorithm Comparison */}
        <motion.div
          className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <h2 className="text-xl font-semibold text-white mb-6">
            Comparaison des Algorithmes
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={algorithmComparison}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="algorithm" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                    color: '#ffffff'
                  }}
                  formatter={(value: any, name: string) => [
                    name === 'accuracy' ? formatPercentage(value) : `${value}%`,
                    name === 'accuracy' ? 'Précision' : 'Vitesse'
                  ]}
                />
                <Bar dataKey="accuracy" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                <Bar dataKey="speed" fill="#10b981" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Model Info */}
        {modelStats && (
          <motion.div
            className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            <h2 className="text-xl font-semibold text-white mb-6">
              Informations du Modèle Actuel
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="space-y-2">
                <div className="text-space-400 text-sm">Échantillons d'Entraînement</div>
                <div className="text-2xl font-bold text-white">
                  {modelStats.training_samples.toLocaleString()}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="text-space-400 text-sm">Dernier Entraînement</div>
                <div className="text-lg text-white">
                  {formatDate(modelStats.last_trained)}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="text-space-400 text-sm">Statut</div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-green-400 font-medium">Opérationnel</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default StatsPage;

