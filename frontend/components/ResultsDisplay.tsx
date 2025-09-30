'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { 
  Download, Eye, EyeOff, TrendingUp, Target, AlertTriangle, 
  CheckCircle2, Clock, Info 
} from 'lucide-react';
import { PredictionResult, AnalysisResult } from '@/types';
import { 
  formatPercentage, 
  formatNumber, 
  getClassificationColor, 
  getClassificationBadgeColor,
  downloadCSV 
} from '@/lib/utils';

interface ResultsDisplayProps {
  results: AnalysisResult;
  onClose?: () => void;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results, onClose }) => {
  const [selectedPrediction, setSelectedPrediction] = useState<PredictionResult | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  // Calcul des statistiques
  const stats = React.useMemo(() => {
    const confirmed = results.predictions.filter(p => p.classification === 'CONFIRMED').length;
    const candidates = results.predictions.filter(p => p.classification === 'CANDIDATE').length;
    const falsePositives = results.predictions.filter(p => p.classification === 'FALSE POSITIVE').length;
    const avgConfidence = results.predictions.reduce((acc, p) => acc + p.confidence_score, 0) / results.predictions.length;

    return {
      confirmed,
      candidates,
      falsePositives,
      avgConfidence,
      total: results.total_samples
    };
  }, [results]);

  // Données pour le graphique en secteurs
  const pieData = [
    { name: 'Confirmées', value: stats.confirmed, color: '#10b981' },
    { name: 'Candidates', value: stats.candidates, color: '#f59e0b' },
    { name: 'Faux Positifs', value: stats.falsePositives, color: '#ef4444' }
  ];

  // Données pour le graphique de confiance
  const confidenceData = results.predictions.map((pred, index) => ({
    index: index + 1,
    confidence: pred.confidence_score,
    classification: pred.classification
  }));

  const exportResults = () => {
    const exportData = results.predictions.map((pred, index) => ({
      'Index': index + 1,
      'Classification': pred.classification,
      'Score de Confiance': formatNumber(pred.confidence_score, 3),
      'Explication': pred.explanation,
      ...Object.entries(pred.features_importance).reduce((acc, [key, value]) => ({
        ...acc,
        [`Importance_${key}`]: formatNumber(value, 3)
      }), {})
    }));

    downloadCSV(exportData, `exoplanet_predictions_${new Date().toISOString().split('T')[0]}.csv`);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 50 }}
      className="space-y-6"
    >
      {/* En-tête des résultats */}
      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">
              Résultats de l'analyse
            </h2>
            <p className="text-space-400">
              {results.total_samples} objets analysés en {results.processing_time}
            </p>
          </div>
          
          <div className="flex items-center space-x-3 mt-4 sm:mt-0">
            <motion.button
              onClick={() => setShowDetails(!showDetails)}
              className="btn-secondary flex items-center space-x-2"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {showDetails ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              <span>{showDetails ? 'Masquer' : 'Détails'}</span>
            </motion.button>
            
            <motion.button
              onClick={exportResults}
              className="btn-primary flex items-center space-x-2"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Download className="h-4 w-4" />
              <span>Exporter</span>
            </motion.button>
          </div>
        </div>

        {/* Statistiques rapides */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <motion.div 
            className="bg-green-500/10 border border-green-500/30 rounded-lg p-4"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="h-8 w-8 text-green-400" />
              <div>
                <p className="text-2xl font-bold text-green-400">{stats.confirmed}</p>
                <p className="text-sm text-space-400">Confirmées</p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center space-x-3">
              <Clock className="h-8 w-8 text-yellow-400" />
              <div>
                <p className="text-2xl font-bold text-yellow-400">{stats.candidates}</p>
                <p className="text-sm text-space-400">Candidates</p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            className="bg-red-500/10 border border-red-500/30 rounded-lg p-4"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center space-x-3">
              <AlertTriangle className="h-8 w-8 text-red-400" />
              <div>
                <p className="text-2xl font-bold text-red-400">{stats.falsePositives}</p>
                <p className="text-sm text-space-400">Faux Positifs</p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            className="bg-primary-500/10 border border-primary-500/30 rounded-lg p-4"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center space-x-3">
              <Target className="h-8 w-8 text-primary-400" />
              <div>
                <p className="text-2xl font-bold text-primary-400">
                  {formatPercentage(stats.avgConfidence)}
                </p>
                <p className="text-sm text-space-400">Confiance Moy.</p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Graphiques */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Graphique en secteurs */}
        <motion.div 
          className="card"
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4">
            Distribution des Classifications
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
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

        {/* Graphique de confiance */}
        <motion.div 
          className="card"
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4">
            Scores de Confiance
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={confidenceData.slice(0, 20)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis 
                  dataKey="index" 
                  stroke="#94a3b8"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#94a3b8"
                  fontSize={12}
                  domain={[0, 1]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                    color: '#ffffff'
                  }}
                  formatter={(value: any) => [formatPercentage(value), 'Confiance']}
                />
                <Bar 
                  dataKey="confidence" 
                  fill="#3b82f6"
                  radius={[2, 2, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Liste détaillée des résultats */}
      <AnimatePresence>
        {showDetails && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="card"
          >
            <h3 className="text-lg font-semibold text-white mb-4">
              Détails des Prédictions
            </h3>
            
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {results.predictions.map((prediction, index) => (
                <motion.div
                  key={index}
                  className="bg-space-800/30 border border-space-600 rounded-lg p-4 hover:border-primary-500/50 cursor-pointer transition-all"
                  whileHover={{ scale: 1.01 }}
                  onClick={() => setSelectedPrediction(
                    selectedPrediction?.explanation === prediction.explanation ? null : prediction
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-space-400 font-mono">#{index + 1}</span>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getClassificationBadgeColor(prediction.classification)}`}>
                        {prediction.classification}
                      </span>
                      <span className="text-white font-medium">
                        {formatPercentage(prediction.confidence_score)}
                      </span>
                    </div>
                    <Info className="h-4 w-4 text-space-400" />
                  </div>
                  
                  <AnimatePresence>
                    {selectedPrediction?.explanation === prediction.explanation && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-4 pt-4 border-t border-space-600"
                      >
                        <p className="text-space-300 text-sm mb-3">
                          {prediction.explanation}
                        </p>
                        
                        <div className="grid grid-cols-2 gap-3">
                          {Object.entries(prediction.features_importance).map(([feature, importance]) => (
                            <div key={feature} className="flex justify-between items-center">
                              <span className="text-space-400 text-xs">{feature}</span>
                              <div className="flex items-center space-x-2">
                                <div className="w-16 bg-space-700 rounded-full h-2">
                                  <div 
                                    className="bg-primary-500 h-2 rounded-full"
                                    style={{ width: `${importance * 100}%` }}
                                  />
                                </div>
                                <span className="text-white text-xs font-mono">
                                  {formatNumber(importance, 2)}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default ResultsDisplay;



