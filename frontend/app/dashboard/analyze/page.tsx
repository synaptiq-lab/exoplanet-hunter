'use client';

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Sparkles,
  Download,
  FileText,
  Star
} from 'lucide-react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';

interface ProcessingStage {
  id: string;
  label: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  message?: string;
}

export default function AnalyzePage() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [stages, setStages] = useState<ProcessingStage[]>([]);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string>('');

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setError('');
    setResults(null);
    setIsProcessing(true);

    // Initialiser les étapes
    setStages([
      { id: 'upload', label: '📤 Upload et validation', status: 'processing' },
      { id: 'train', label: '🧠 Entraînement du modèle', status: 'pending' },
      { id: 'validate', label: '🔍 Validation des planètes', status: 'pending' },
      { id: 'results', label: '✨ Résultats', status: 'pending' }
    ]);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Simuler la progression visuelle pendant le traitement backend
      // Upload complété après 1.5s
      const uploadSimulation = setTimeout(() => {
        updateStage('upload', 'completed', 'CSV validé et analysé');
      }, 1500);

      // Train démarre après 2s et reste en "processing" jusqu'à la réponse
      const trainSimulation = setTimeout(() => {
        updateStage('train', 'processing', 'Entraînement du modèle en cours...');
      }, 2000);

      // Pas de completion automatique du train - on attend la vraie réponse

      // Appel à l'endpoint unique qui fait tout
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData
      });

      // Annuler les simulations
      clearTimeout(uploadSimulation);
      clearTimeout(trainSimulation);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de l\'analyse');
      }

      const data = await response.json();
      
      // Mettre à jour les étapes avec les vraies données
      updateStage('upload', 'completed', `${data.csv_info.format_name} - ${data.csv_info.row_count} objets`);
      updateStage('train', 'completed', `Précision: ${(data.training.accuracy * 100).toFixed(1)}%`);
      updateStage('validate', 'completed', `${data.validation.analysis_summary.confirmed_count} planètes confirmées`);
      updateStage('results', 'completed');
      
      setResults(data);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
      const processingStage = stages.find(s => s.status === 'processing');
      if (processingStage) {
        updateStage(processingStage.id, 'error', err instanceof Error ? err.message : 'Erreur');
      }
    } finally {
      setIsProcessing(false);
    }
  }, [stages]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    multiple: false,
    disabled: isProcessing
  });

  const updateStage = (id: string, status: ProcessingStage['status'], message?: string) => {
    setStages(prev => prev.map(stage => 
      stage.id === id ? { ...stage, status, message } : stage
    ));
  };

  const resetAnalysis = () => {
    setIsProcessing(false);
    setStages([]);
    setResults(null);
    setError('');
  };

  const getStageIcon = (status: ProcessingStage['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-400" />;
      case 'processing':
        return <Loader2 className="h-5 w-5 text-primary-400 animate-spin" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-400" />;
      default:
        return <div className="h-5 w-5 rounded-full border-2 border-space-600" />;
    }
  };

  const exportResults = () => {
    if (!results?.validation?.confirmed_planets) return;

    const csvContent = [
      ['Nom', 'Statut Original', 'Confiance', 'Période (j)', 'Rayon (R⊕)'],
      ...results.validation.confirmed_planets.map((planet: any) => [
        planet.name,
        planet.original_status,
        (planet.confidence * 100).toFixed(1) + '%',
        planet.characteristics.period?.toFixed(3) || 'N/A',
        planet.characteristics.radius?.toFixed(2) || 'N/A'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `exoplanetes_confirmees_${new Date().getTime()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <DashboardLayout>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-5xl font-bold gradient-text mb-4">
            🌌 Exoplanet Hunter
          </h1>
          <p className="text-space-300 text-xl">
            Détection automatique d'exoplanètes par IA
          </p>
        </motion.div>

        {/* Upload Zone (visible si pas de traitement en cours et pas de résultats) */}
        {!isProcessing && !results && !error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-8"
          >
            <div
              {...getRootProps()}
              className={`card p-12 border-2 border-dashed cursor-pointer transition-all ${
                isDragActive 
                  ? 'border-primary-500 bg-primary-500/10' 
                  : 'border-space-600 hover:border-primary-500'
              }`}
            >
              <input {...getInputProps()} />
              <div className="text-center">
                <motion.div
                  animate={{ 
                    y: isDragActive ? -10 : 0,
                    scale: isDragActive ? 1.1 : 1
                  }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <Upload className="h-24 w-24 text-primary-400 mx-auto mb-6" />
                </motion.div>
                
                <h3 className="text-2xl font-bold text-white mb-3">
                  {isDragActive 
                    ? 'Déposez le fichier ici' 
                    : 'Glissez-déposez votre fichier CSV'
                  }
                </h3>
                
                <p className="text-space-400 text-lg mb-4">
                  ou cliquez pour sélectionner
                </p>
                
                <div className="inline-flex items-center space-x-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-semibold transition-colors">
                  <Sparkles className="h-5 w-5" />
                  <span>Sélectionner un fichier CSV</span>
                </div>
                
                <div className="mt-6 space-y-2">
                  <p className="text-space-500 text-sm">
                    <strong className="text-space-400">Formats supportés:</strong> Kepler (KOI), K2, TESS (TOI)
                  </p>
                  <p className="text-space-500 text-sm">
                    L'analyse complète démarre automatiquement après l'upload
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Processing Stages */}
        {isProcessing && stages.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card p-8 mb-8"
          >
            <h3 className="text-2xl font-semibold text-white mb-6 flex items-center">
              <Loader2 className="h-6 w-6 text-primary-400 mr-3 animate-spin" />
              Traitement en cours...
            </h3>

            <div className="space-y-4">
              {stages.map((stage, index) => (
                <motion.div
                  key={stage.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`flex items-center space-x-4 p-4 rounded-lg transition-all ${
                    stage.status === 'completed' ? 'bg-green-500/10 border border-green-500/30' :
                    stage.status === 'processing' ? 'bg-primary-500/10 border border-primary-500/30' :
                    stage.status === 'error' ? 'bg-red-500/10 border border-red-500/30' :
                    'bg-space-700/30'
                  }`}
                >
                  {getStageIcon(stage.status)}
                  <div className="flex-1">
                    <div className="font-semibold text-white text-lg">{stage.label}</div>
                    {stage.message && (
                      <div className="text-sm text-space-400 mt-1">{stage.message}</div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Error Display */}
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card p-8 mb-8 border-2 border-red-500/30"
          >
            <div className="flex items-start space-x-4">
              <AlertCircle className="h-8 w-8 text-red-400 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-red-400 mb-2">Erreur</h3>
                <p className="text-red-300 mb-4">{error}</p>
                <button
                  onClick={resetAnalysis}
                  className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors"
                >
                  Réessayer
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Results Display */}
        {results && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {/* Header with Actions */}
            <div className="card p-6 mb-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-3xl font-bold text-white flex items-center">
                    <Star className="h-8 w-8 text-primary-400 mr-3" />
                    Résultats de l'analyse
                  </h2>
                  <p className="text-space-400 mt-1">
                    {results.csv_info.filename} • {results.csv_info.format_name}
                  </p>
                </div>
                <div className="flex space-x-3">
                  {results.validation.confirmed_planets.length > 0 && (
                    <button
                      onClick={exportResults}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-colors flex items-center space-x-2"
                    >
                      <Download className="h-5 w-5" />
                      <span>Exporter CSV</span>
                    </button>
                  )}
                  <button
                    onClick={resetAnalysis}
                    className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-semibold transition-colors"
                  >
                    Nouvelle analyse
                  </button>
                </div>
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-space-700/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-white">
                    {results.csv_info.row_count}
                  </div>
                  <div className="text-space-400 text-sm">Objets</div>
                </div>
                <div className="bg-space-700/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-primary-400">
                    {(results.training.accuracy * 100).toFixed(1)}%
                  </div>
                  <div className="text-space-400 text-sm">Précision</div>
                </div>
                <div className="bg-space-700/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-white">
                    {results.validation.analysis_summary.total_analyzed}
                  </div>
                  <div className="text-space-400 text-sm">Analysées</div>
                </div>
                <div className="bg-green-500/20 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-green-400">
                    {results.validation.analysis_summary.confirmed_count}
                  </div>
                  <div className="text-space-400 text-sm">Confirmées</div>
                </div>
                <div className="bg-primary-500/20 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-primary-400">
                    {(results.validation.analysis_summary.confirmation_rate * 100).toFixed(1)}%
                  </div>
                  <div className="text-space-400 text-sm">Taux</div>
                </div>
              </div>
            </div>

            {/* Confirmed Planets Table */}
            {results.validation.confirmed_planets.length > 0 ? (
              <div className="card p-6">
                <h3 className="text-2xl font-bold text-white mb-4 flex items-center">
                  <CheckCircle className="h-6 w-6 text-green-400 mr-2" />
                  Exoplanètes Confirmées ({results.validation.confirmed_planets.length})
                </h3>
                
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-space-700">
                        <th className="text-left py-3 px-4 text-space-300 font-semibold">Planète</th>
                        <th className="text-left py-3 px-4 text-space-300 font-semibold">Statut Original</th>
                        <th className="text-left py-3 px-4 text-space-300 font-semibold">Confiance</th>
                        <th className="text-left py-3 px-4 text-space-300 font-semibold">Période (j)</th>
                        <th className="text-left py-3 px-4 text-space-300 font-semibold">Rayon (R⊕)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.validation.confirmed_planets.slice(0, 50).map((planet: any, index: number) => (
                        <motion.tr
                          key={index}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="border-b border-space-700/50 hover:bg-space-700/20 transition-colors"
                        >
                          <td className="py-3 px-4">
                            <div className="flex items-center space-x-2">
                              <Star className="h-4 w-4 text-primary-400" />
                              <span className="font-semibold text-white">{planet.name}</span>
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-sm font-medium">
                              {planet.original_status}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="text-green-400 font-bold">
                              {(planet.confidence * 100).toFixed(1)}%
                            </span>
                          </td>
                          <td className="py-3 px-4 text-space-300">
                            {planet.characteristics.period?.toFixed(3) || 'N/A'}
                          </td>
                          <td className="py-3 px-4 text-space-300">
                            {planet.characteristics.radius?.toFixed(2) || 'N/A'}
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                  
                  {results.validation.confirmed_planets.length > 50 && (
                    <div className="text-center mt-6 p-4 bg-primary-500/10 rounded-lg border border-primary-500/30">
                      <p className="text-primary-400 font-semibold mb-1">
                        + {results.validation.confirmed_planets.length - 50} autres planètes confirmées
                      </p>
                      <p className="text-space-400 text-sm">
                        Exportez le fichier CSV pour obtenir la liste complète des {results.validation.confirmed_planets.length} planètes
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="card p-12 text-center">
                <AlertCircle className="h-16 w-16 text-space-500 mx-auto mb-4" />
                <h3 className="text-2xl font-semibold text-white mb-2">
                  Aucune nouvelle exoplanète confirmée
                </h3>
                <p className="text-space-400">
                  Le modèle n'a trouvé aucun candidat avec une confiance suffisante pour être confirmé
                </p>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  );
}
