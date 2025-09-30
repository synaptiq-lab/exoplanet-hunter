'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, 
  XCircle, 
  Star, 
  Clock, 
  Zap, 
  Globe,
  X,
  Download,
  Eye
} from 'lucide-react';

interface Planet {
  name: string;
  original_status: string;
  predicted_status: string;
  confidence: number;
  characteristics: {
    period: number;
    duration: number;
    depth: number;
    radius: number;
  };
}

interface ValidationResults {
  message: string;
  confirmed_planets: Planet[];
  rejected_planets: Planet[];
  analysis_summary: {
    total_analyzed: number;
    confirmed_count: number;
    rejected_count: number;
    confirmation_rate: number;
  };
}

interface ExoplanetValidationResultsProps {
  results: ValidationResults | null;
  isOpen: boolean;
  onClose: () => void;
  datasetName?: string;
}

const ExoplanetValidationResults: React.FC<ExoplanetValidationResultsProps> = ({
  results,
  isOpen,
  onClose,
  datasetName
}) => {
  if (!results) return null;

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-orange-400';
  };

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-500/20';
    if (confidence >= 0.6) return 'bg-yellow-500/20';
    return 'bg-orange-500/20';
  };

  const exportResults = () => {
    const csvContent = [
      ['Nom de la Planète', 'Statut Original', 'Statut Prédit', 'Confiance', 'Période (jours)', 'Durée (h)', 'Profondeur (ppm)', 'Rayon (R⊕)'],
      ...results.confirmed_planets.map(planet => [
        planet.name,
        planet.original_status,
        planet.predicted_status,
        (planet.confidence * 100).toFixed(1) + '%',
        planet.characteristics.period?.toFixed(3) || 'N/A',
        planet.characteristics.duration?.toFixed(3) || 'N/A',
        planet.characteristics.depth?.toFixed(1) || 'N/A',
        planet.characteristics.radius?.toFixed(2) || 'N/A'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `exoplanetes_confirmees_${datasetName || 'dataset'}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            className="bg-space-800 border border-space-700 rounded-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-space-700">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center">
                  <Star className="h-6 w-6 text-primary-400 mr-2" />
                  Résultats de Validation d'Exoplanètes
                </h2>
                <p className="text-space-300 mt-1">{results.message}</p>
              </div>
              
              <div className="flex items-center space-x-3">
                <motion.button
                  onClick={exportResults}
                  className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
                  whileHover={{ scale: 1.05 }}
                >
                  <Download className="h-4 w-4" />
                  <span>Exporter CSV</span>
                </motion.button>
                
                <motion.button
                  onClick={onClose}
                  className="p-2 text-space-400 hover:text-white transition-colors"
                  whileHover={{ scale: 1.1 }}
                >
                  <X className="h-5 w-5" />
                </motion.button>
              </div>
            </div>

            {/* Summary Stats */}
            <div className="p-6 border-b border-space-700">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-space-700/30 rounded-xl p-4 text-center">
                  <div className="text-2xl font-bold text-white">{results.analysis_summary.total_analyzed}</div>
                  <div className="text-space-400 text-sm">Planètes Analysées</div>
                </div>
                <div className="bg-green-500/20 rounded-xl p-4 text-center">
                  <div className="text-2xl font-bold text-green-400">{results.analysis_summary.confirmed_count}</div>
                  <div className="text-space-400 text-sm">Confirmées</div>
                </div>
                <div className="bg-red-500/20 rounded-xl p-4 text-center">
                  <div className="text-2xl font-bold text-red-400">{results.analysis_summary.rejected_count}</div>
                  <div className="text-space-400 text-sm">Rejetées</div>
                </div>
                <div className="bg-primary-500/20 rounded-xl p-4 text-center">
                  <div className="text-2xl font-bold text-primary-400">
                    {(results.analysis_summary.confirmation_rate * 100).toFixed(1)}%
                  </div>
                  <div className="text-space-400 text-sm">Taux de Confirmation</div>
                </div>
              </div>
            </div>

            {/* Results Content */}
            <div className="p-6 overflow-y-auto max-h-96">
              {results.confirmed_planets.length > 0 ? (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                      <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
                      Nouvelles Exoplanètes Confirmées ({results.confirmed_planets.length})
                    </h3>
                    
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-space-700">
                            <th className="text-left py-3 px-4 text-space-300 font-medium">Nom de la Planète</th>
                            <th className="text-left py-3 px-4 text-space-300 font-medium">Statut Original</th>
                            <th className="text-left py-3 px-4 text-space-300 font-medium">Confiance</th>
                            <th className="text-left py-3 px-4 text-space-300 font-medium">Période (jours)</th>
                            <th className="text-left py-3 px-4 text-space-300 font-medium">Durée (h)</th>
                            <th className="text-left py-3 px-4 text-space-300 font-medium">Rayon (R⊕)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {results.confirmed_planets.map((planet, index) => (
                            <motion.tr
                              key={planet.name}
                              className="border-b border-space-700/50 hover:bg-space-700/20 transition-colors"
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: index * 0.1 }}
                            >
                              <td className="py-4 px-4">
                                <div className="flex items-center space-x-2">
                                  <Star className="h-4 w-4 text-primary-400" />
                                  <span className="font-medium text-white">{planet.name}</span>
                                </div>
                              </td>
                              <td className="py-4 px-4">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  planet.original_status === 'CANDIDATE' 
                                    ? 'bg-yellow-500/20 text-yellow-400' 
                                    : 'bg-red-500/20 text-red-400'
                                }`}>
                                  {planet.original_status}
                                </span>
                              </td>
                              <td className="py-4 px-4">
                                <div className="flex items-center space-x-2">
                                  <div className={`w-2 h-2 rounded-full ${getConfidenceBg(planet.confidence)}`}></div>
                                  <span className={`font-medium ${getConfidenceColor(planet.confidence)}`}>
                                    {(planet.confidence * 100).toFixed(1)}%
                                  </span>
                                </div>
                              </td>
                              <td className="py-4 px-4 text-space-300">
                                <div className="flex items-center space-x-1">
                                  <Clock className="h-3 w-3" />
                                  <span>{planet.characteristics.period?.toFixed(3) || 'N/A'}</span>
                                </div>
                              </td>
                              <td className="py-4 px-4 text-space-300">
                                <div className="flex items-center space-x-1">
                                  <Zap className="h-3 w-3" />
                                  <span>{planet.characteristics.duration?.toFixed(3) || 'N/A'}</span>
                                </div>
                              </td>
                              <td className="py-4 px-4 text-space-300">
                                <div className="flex items-center space-x-1">
                                  <Globe className="h-3 w-3" />
                                  <span>{planet.characteristics.radius?.toFixed(2) || 'N/A'}</span>
                                </div>
                              </td>
                            </motion.tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Rejected Planets Summary */}
                  {results.rejected_planets.length > 0 && (
                    <div className="pt-6 border-t border-space-700">
                      <h3 className="text-lg font-semibold text-white mb-2 flex items-center">
                        <XCircle className="h-5 w-5 text-red-400 mr-2" />
                        Planètes Rejetées ({results.rejected_planets.length})
                      </h3>
                      <p className="text-space-400 text-sm">
                        Ces planètes n'ont pas les caractéristiques suffisantes pour être confirmées comme exoplanètes.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <XCircle className="h-16 w-16 text-space-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">
                    Aucune Nouvelle Exoplanète Confirmée
                  </h3>
                  <p className="text-space-400">
                    Aucune planète CANDIDATE ou FALSE POSITIVE n'a pu être confirmée dans ce dataset.
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ExoplanetValidationResults;
