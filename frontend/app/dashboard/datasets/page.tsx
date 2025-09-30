'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { 
  Upload, 
  Database, 
  Trash2, 
  BarChart3, 
  Settings, 
  Eye,
  Calendar,
  FileText,
  AlertCircle,
  CheckCircle,
  Loader2,
  Download,
  Plus
} from 'lucide-react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import FileUpload from '@/components/FileUpload';
import ExoplanetValidationResults from '@/components/ExoplanetValidationResults';
import { UploadStatus } from '@/types';

interface Dataset {
  id: string;
  filename: string;
  upload_date: string;
  rows: number;
  columns: number;
  has_labels: boolean;
  validation: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
  };
}

const DatasetsPage = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
    status: 'idle',
    progress: 0,
    message: ''
  });
  const [actionLoading, setActionLoading] = useState<{[key: string]: string}>({});
  const [validationResults, setValidationResults] = useState<any>(null);
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      const response = await fetch('http://localhost:8000/datasets');
      const data = await response.json();
      setDatasets(data.datasets || []);
    } catch (error) {
      console.error('Erreur lors du chargement des datasets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (file: File) => {
    setUploadStatus({
      status: 'uploading',
      progress: 0,
      message: 'Téléchargement en cours...'
    });

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/datasets/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erreur lors de l\'upload');
      }

      const result = await response.json();
      
      setUploadStatus({
        status: 'success',
        progress: 100,
        message: `Dataset "${result.metadata.filename}" uploadé avec succès`
      });

      // Recharger la liste
      await loadDatasets();
      
      // Fermer le modal d'upload après 2 secondes
      setTimeout(() => {
        setShowUpload(false);
        setUploadStatus({ status: 'idle', progress: 0, message: '' });
      }, 2000);

    } catch (error) {
      setUploadStatus({
        status: 'error',
        progress: 0,
        message: error instanceof Error ? error.message : 'Erreur lors de l\'upload'
      });
    }
  };

  const handleFileRemove = () => {
    setUploadStatus({ status: 'idle', progress: 0, message: '' });
  };

  const deleteDataset = async (datasetId: string) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce dataset ?')) return;

    setActionLoading(prev => ({ ...prev, [datasetId]: 'deleting' }));

    try {
      const response = await fetch(`http://localhost:8000/datasets/${datasetId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la suppression');
      }

      await loadDatasets();
    } catch (error) {
      alert('Erreur lors de la suppression du dataset');
    } finally {
      setActionLoading(prev => {
        const newState = { ...prev };
        delete newState[datasetId];
        return newState;
      });
    }
  };

  const analyzeDataset = async (datasetId: string) => {
    setActionLoading(prev => ({ ...prev, [datasetId]: 'analyzing' }));

    try {
      const dataset = datasets.find(d => d.id === datasetId);
      if (!dataset) {
        throw new Error('Dataset non trouvé');
      }

      // Utiliser l'endpoint de validation spécialisé directement
      // (les datasets sont déjà dans le système)
      const response = await fetch(`http://localhost:8000/validate/${datasetId}`, {
        method: 'POST'
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erreur lors de la validation des exoplanètes');
      }

      const result = await response.json();
      
      // Afficher les résultats dans le modal
      setValidationResults(result);
      setShowResults(true);
      
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Erreur lors de l\'analyse');
    } finally {
      setActionLoading(prev => {
        const newState = { ...prev };
        delete newState[datasetId];
        return newState;
      });
    }
  };

  const trainOnDataset = async (datasetId: string) => {
    const dataset = datasets.find(d => d.id === datasetId);
    if (!dataset?.has_labels) {
      alert('Ce dataset ne contient pas de labels nécessaires pour l\'entraînement');
      return;
    }

    setActionLoading(prev => ({ ...prev, [datasetId]: 'training' }));

    try {
      const config = {
        algorithm: 'xgboost',
        test_size: 0.3,
        random_state: 42,
        hyperparameters: {}
      };

      const formData = new FormData();
      formData.append('config', JSON.stringify(config));

      const response = await fetch(`http://localhost:8000/datasets/${datasetId}/train`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erreur lors de l\'entraînement');
      }

      const result = await response.json();
      
      alert(`Entraînement terminé !\nNouvelle précision: ${(result.new_stats.accuracy * 100).toFixed(1)}%\nÉchantillons utilisés: ${result.samples_used}`);
      
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Erreur lors de l\'entraînement');
    } finally {
      setActionLoading(prev => {
        const newState = { ...prev };
        delete newState[datasetId];
        return newState;
      });
    }
  };

  const getStatusIcon = (dataset: Dataset) => {
    if (!dataset.validation.is_valid) {
      return <AlertCircle className="h-5 w-5 text-red-400" />;
    }
    if (dataset.validation.warnings.length > 0) {
      return <AlertCircle className="h-5 w-5 text-yellow-400" />;
    }
    return <CheckCircle className="h-5 w-5 text-green-400" />;
  };

  const getStatusColor = (dataset: Dataset) => {
    if (!dataset.validation.is_valid) {
      return 'border-red-500/50 bg-red-500/5';
    }
    if (dataset.validation.warnings.length > 0) {
      return 'border-yellow-500/50 bg-yellow-500/5';
    }
    return 'border-green-500/50 bg-green-500/5';
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Gestion des Datasets
            </h1>
            <p className="text-space-300">
              Téléversez, analysez et entraînez vos modèles sur vos datasets d'exoplanètes
            </p>
          </div>
          
          <motion.button
            onClick={() => setShowUpload(true)}
            className="flex items-center space-x-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-xl font-medium transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Plus className="h-5 w-5" />
            <span>Nouveau Dataset</span>
          </motion.button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <Database className="h-8 w-8 text-blue-400" />
              <span className="text-2xl font-bold text-white">{datasets.length}</span>
            </div>
            <p className="text-space-400 mt-2">Datasets Total</p>
          </div>
          
          <div className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <FileText className="h-8 w-8 text-green-400" />
              <span className="text-2xl font-bold text-white">
                {datasets.reduce((sum, d) => sum + d.rows, 0).toLocaleString()}
              </span>
            </div>
            <p className="text-space-400 mt-2">Lignes Total</p>
          </div>
          
          <div className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <CheckCircle className="h-8 w-8 text-purple-400" />
              <span className="text-2xl font-bold text-white">
                {datasets.filter(d => d.has_labels).length}
              </span>
            </div>
            <p className="text-space-400 mt-2">Avec Labels</p>
          </div>
          
          <div className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <AlertCircle className="h-8 w-8 text-red-400" />
              <span className="text-2xl font-bold text-white">
                {datasets.filter(d => !d.validation.is_valid).length}
              </span>
            </div>
            <p className="text-space-400 mt-2">Avec Erreurs</p>
          </div>
        </div>

        {/* Datasets Grid */}
        {datasets.length === 0 ? (
          <motion.div
            className="text-center py-12 bg-space-800/20 rounded-xl border border-space-700"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <Database className="h-16 w-16 text-space-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              Aucun dataset
            </h3>
            <p className="text-space-400 mb-6">
              Commencez par téléverser votre premier dataset CSV
            </p>
            <motion.button
              onClick={() => setShowUpload(true)}
              className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
              whileHover={{ scale: 1.05 }}
            >
              Téléverser un Dataset
            </motion.button>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {datasets.map((dataset, index) => (
              <motion.div
                key={dataset.id}
                className={`bg-space-800/30 backdrop-blur-sm border rounded-xl p-6 ${getStatusColor(dataset)}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{ scale: 1.02, y: -5 }}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <Database className="h-6 w-6 text-primary-400" />
                    <div>
                      <h3 className="font-semibold text-white truncate max-w-48">
                        {dataset.filename}
                      </h3>
                      <p className="text-space-400 text-sm">ID: {dataset.id}</p>
                    </div>
                  </div>
                  {getStatusIcon(dataset)}
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="text-center p-3 bg-space-700/30 rounded-lg">
                    <div className="text-lg font-bold text-white">{dataset.rows.toLocaleString()}</div>
                    <div className="text-space-400 text-xs">Lignes</div>
                  </div>
                  <div className="text-center p-3 bg-space-700/30 rounded-lg">
                    <div className="text-lg font-bold text-white">{dataset.columns}</div>
                    <div className="text-space-400 text-xs">Colonnes</div>
                  </div>
                </div>

                {/* Labels Badge */}
                <div className="flex items-center justify-between mb-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    dataset.has_labels 
                      ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                      : 'bg-gray-500/20 text-gray-400 border border-gray-500/50'
                  }`}>
                    {dataset.has_labels ? '✓ Avec Labels' : 'Sans Labels'}
                  </span>
                  
                  <div className="flex items-center space-x-1 text-space-500 text-xs">
                    <Calendar className="h-3 w-3" />
                    <span>{new Date(dataset.upload_date).toLocaleDateString('fr-FR')}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="space-y-2">
                  <div className="flex space-x-2">
                    <motion.button
                      onClick={() => analyzeDataset(dataset.id)}
                      disabled={!!actionLoading[dataset.id]}
                      className="flex-1 flex items-center justify-center space-x-2 p-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      {actionLoading[dataset.id] === 'analyzing' ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <BarChart3 className="h-4 w-4" />
                      )}
                      <span className="text-sm">Valider Planètes</span>
                    </motion.button>

                    <motion.button
                      onClick={() => trainOnDataset(dataset.id)}
                      disabled={!dataset.has_labels || !!actionLoading[dataset.id]}
                      className="flex-1 flex items-center justify-center space-x-2 p-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-colors disabled:opacity-50"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      {actionLoading[dataset.id] === 'training' ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Settings className="h-4 w-4" />
                      )}
                      <span className="text-sm">Entraîner</span>
                    </motion.button>
                  </div>

                  <div className="flex space-x-2">
                    <Link href={`/dashboard/datasets/${dataset.id}/explore`} className="flex-1">
                      <motion.button
                        className="w-full flex items-center justify-center space-x-2 p-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <Eye className="h-4 w-4" />
                        <span className="text-sm">Explorer</span>
                      </motion.button>
                    </Link>

                    <motion.button
                      onClick={() => deleteDataset(dataset.id)}
                      disabled={!!actionLoading[dataset.id]}
                      className="p-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors disabled:opacity-50"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      {actionLoading[dataset.id] === 'deleting' ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </motion.button>
                  </div>
                </div>

                {/* Validation Messages */}
                {(dataset.validation.errors.length > 0 || dataset.validation.warnings.length > 0) && (
                  <div className="mt-4 pt-4 border-t border-space-600">
                    {dataset.validation.errors.length > 0 && (
                      <div className="text-red-400 text-xs mb-1">
                        ❌ {dataset.validation.errors[0]}
                      </div>
                    )}
                    {dataset.validation.warnings.length > 0 && (
                      <div className="text-yellow-400 text-xs">
                        ⚠️ {dataset.validation.warnings[0]}
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}

        {/* Upload Modal */}
        <AnimatePresence>
          {showUpload && (
            <motion.div
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div
                className="bg-space-800 border border-space-700 rounded-2xl p-8 w-full max-w-2xl"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
              >
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-white">
                    Téléverser un Dataset
                  </h2>
                  <motion.button
                    onClick={() => setShowUpload(false)}
                    className="p-2 text-space-400 hover:text-white transition-colors"
                    whileHover={{ scale: 1.1 }}
                  >
                    ✕
                  </motion.button>
                </div>

                <FileUpload
                  onFileSelect={handleFileSelect}
                  onFileRemove={handleFileRemove}
                  uploadStatus={uploadStatus}
                />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Validation Results Modal */}
        <ExoplanetValidationResults
          results={validationResults}
          isOpen={showResults}
          onClose={() => {
            setShowResults(false);
            setValidationResults(null);
          }}
          datasetName={datasets.find(d => validationResults?.dataset_id === d.id)?.filename}
        />
      </div>
    </DashboardLayout>
  );
};

export default DatasetsPage;

