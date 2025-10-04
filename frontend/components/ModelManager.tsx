'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  RefreshCw, 
  Download, 
  Upload, 
  Trash2, 
  HardDrive, 
  Server,
  Info,
  AlertCircle
} from 'lucide-react';
import { apiClient } from '@/lib/api';

interface LocalStorageModel {
  format_type: string;
  filename: string;
  available: boolean;
  last_modified: string | null;
}

interface StoredModel {
  format_type: string;
  model_json: any;
  metadata: any;
}

export default function ModelManager() {
    const [serverModels, setServerModels] = useState<LocalStorageModel[]>([]);
    const [localModels, setLocalModels] = useState<Record<string, StoredModel>>({});
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState('');

    // Charger les modèles au montage
    useEffect(() => {
      loadModels();
      loadLocalModels();
    }, []);

    const loadModels = async () => {
      try {
        setLoading(true);
        const result = await apiClient.listLocalStorageModels();
        setServerModels(result.available_models);
      } catch (error) {
        setMessage(`Erreur lors du chargement des modèles serveur: ${error}`);
      } finally {
        setLoading(false);
      }
    };

    const loadLocalModels = () => {
      const storedModels: any = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('exoplanet_model_')) {
          try {
            const modelData = JSON.parse(localStorage.getItem(key)!);
            const formatType = key.replace('exoplanet_model_', '');
            storedModels[formatType] = modelData;
          } catch (error) {
            console.warn(`Erreur parsing modèle localStorage ${key}:`, error);
          }
        }
      }
      setLocalModels(storedModels);
    };

    const downloadModelToLocalStorage = async (formatType: string) => {
      try {
        const modelData = await apiClient.downloadModelForLocalStorage(formatType);
        
        // Sauvegarder en localStorage
        localStorage.setItem(`exoplanet_model_${formatType}`, JSON.stringify(modelData));
        
        setMessage(`✅ Modèle ${formatType} téléchargé et sauvegardé en localStorage`);
        loadLocalModels(); // Rafraîchir la liste
      } catch (error) {
        setMessage(`❌ Erreur lors du téléchargement du modèle ${formatType}: ${error}`);
      }
    };

    const uploadModelToServer = async (formatType: string) => {
      try {
        const modelData = JSON.parse(localStorage.getItem(`exoplanet_model_${formatType}`)!);
        await apiClient.uploadModelFromLocalStorage(modelData);
        setMessage(`✅ Modèle ${formatType} uploadé vers le serveur`);
        loadModels(); // Rafraîchir la liste
      } catch (error) {
        setMessage(`❌ Erreur lors de l'upload du modèle ${formatType}: ${error}`);
      }
    };

    const deleteModelFromLocalStorage = (formatType: string) => {
      if (confirm(`Supprimer le modèle ${formatType} du localStorage ?`)) {
        localStorage.removeItem(`exoplanet_model_${formatType}`);
        setMessage(`🗑️ Modèle ${formatType} supprimé du localStorage`);
        loadLocalModels(); // Rafraîchir la liste
      }
    };

    const clearMessage = () => {
      setTimeout(() => setMessage(''), 5000);
    };

    useEffect(() => {
      if (message) {
        clearMessage();
      }
    }, [message]);

    return (
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div>
            <h1 className="text-4xl font-bold gradient-text mb-2">
              🔧 Gestion des Modèles
            </h1>
            <p className="text-space-300 text-lg">
              Gérez vos modèles entraînés : téléchargez depuis le serveur vers localStorage ou utilisez vos modèles locaux
            </p>
          </div>
          <motion.button
            onClick={() => { loadModels(); loadLocalModels(); }}
            className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-semibold transition-all duration-200 flex items-center space-x-2"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <RefreshCw className="h-5 w-5" />
            <span>Rafraîchir</span>
          </motion.button>
        </motion.div>

        {/* Message de notification */}
        {message && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`card p-4 mb-6 border-l-4 ${
              message.includes('✅') || message.includes('🗑️') 
                ? 'border-green-400 bg-green-500/10' 
                : 'border-red-400 bg-red-500/10'
            }`}
          >
            <div className={`flex items-center space-x-3 ${
              message.includes('✅') || message.includes('🗑️') 
                ? 'text-green-300' 
                : 'text-red-300'
            }`}>
              {message.includes('✅') ? (
                <div className="w-6 h-6 rounded-full bg-green-400 flex items-center justify-center">
                  <span className="text-xs text-white">✓</span>
                </div>
              ) : message.includes('🗑️') ? (
                <Trash2 className="h-5 w-5" />
              ) : (
                <AlertCircle className="h-5 w-5" />
              )}
              <span className="font-medium">{message}</span>
            </div>
          </motion.div>
        )}

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Modèles Serveur */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="card p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-primary-500/20 rounded-lg">
                  <Server className="h-6 w-6 text-primary-400" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">
                    Modèles Serveur
                  </h2>
                  <p className="text-space-400 text-sm">
                    Modèles disponibles pour téléchargement
                  </p>
                </div>
              </div>
              <div className="px-3 py-1 bg-primary-500/20 rounded-full">
                <span className="text-primary-400 font-semibold text-sm">
                  {serverModels.length}
                </span>
              </div>
            </div>
            
            <p className="text-space-300 text-sm mb-6">
              Modèles entraînés disponibles sur le serveur pour téléchargement vers localStorage
            </p>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-400"></div>
                <span className="ml-3 text-space-300">Chargement...</span>
              </div>
            ) : serverModels.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-space-700 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Server className="h-8 w-8 text-space-500" />
                </div>
                <p className="text-space-400 mb-2">Aucun modèle disponible sur le serveur</p>
                <p className="text-space-500 text-sm">Entraînez d'abord un modèle sur un dataset</p>
              </div>
            ) : (
              <div className="space-y-4">
                {serverModels.map((model, index) => (
                  <motion.div
                    key={model.format_type}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 bg-space-700/30 rounded-lg border border-space-600 hover:border-space-500 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-white capitalize mb-1">
                          Modèle {model.format_type}
                        </h3>
                        <p className="text-space-400 text-sm mb-2">
                          {model.filename}
                        </p>
                        {model.last_modified && (
                          <p className="text-xs text-space-500">
                            Modifié: {model.last_modified}
                          </p>
                        )}
                      </div>
                      <motion.button
                        onClick={() => downloadModelToLocalStorage(model.format_type)}
                        disabled={!model.available}
                        className={`px-4 py-2 text-white text-sm rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 ${
                          model.available
                            ? 'bg-green-600 hover:bg-green-700'
                            : 'bg-space-700 text-space-400 cursor-not-allowed'
                        }`}
                        whileHover={model.available ? { scale: 1.05 } : {}}
                        whileTap={model.available ? { scale: 0.95 } : {}}
                      >
                        <Download className="h-4 w-4" />
                        <span>Télécharger</span>
                      </motion.button>
                    </div>
                    {!model.available && (
                      <div className="mt-3 p-2 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400">
                        <div className="flex items-center space-x-2">
                          <AlertCircle className="h-4 w-4" />
                          <span>Fichier modèle non disponible</span>
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>

          {/* Modèles localStorage */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="card p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-green-500/20 rounded-lg">
                  <HardDrive className="h-6 w-6 text-green-400" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">
                    Modèles localStorage
                  </h2>
                  <p className="text-space-400 text-sm">
                    Modèles sauvegardés localement
                  </p>
                </div>
              </div>
              <div className="px-3 py-1 bg-green-500/20 rounded-full">
                <span className="text-green-400 font-semibold text-sm">
                  {Object.keys(localModels).length}
                </span>
              </div>
            </div>
            
            <p className="text-space-300 text-sm mb-6">
              Modèles sauvegardés localement sur votre machine
            </p>

            {Object.keys(localModels).length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-space-700 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <HardDrive className="h-8 w-8 text-space-500" />
                </div>
                <p className="text-space-400 mb-2">Aucun modèle sauvegardé en localStorage</p>
                <p className="text-space-500 text-sm">Téléchargez un modèle depuis le serveur pour commencer</p>
              </div>
            ) : (
              <div className="space-y-4">
                {Object.entries(localModels).map(([formatType, modelData], index) => (
                  <motion.div
                    key={formatType}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 bg-space-700/30 rounded-lg border border-space-600 hover:border-space-500 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="font-semibold text-white capitalize mb-1">
                          Modèle {formatType}
                        </h3>
                        <p className="text-space-400 text-sm mb-1">
                          {modelData.metadata?.feature_columns?.length || 0} features
                        </p>
                        <p className="text-xs text-space-500 mb-2">
                          Classes: {modelData.metadata?.label_encoder_classes?.join(', ') || 'N/A'}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <motion.button
                          onClick={() => uploadModelToServer(formatType)}
                          className="px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm rounded-md font-medium transition-colors flex items-center space-x-1"
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <Upload className="h-4 w-4" />
                          <span>Upload</span>
                        </motion.button>
                        <motion.button
                          onClick={() => deleteModelFromLocalStorage(formatType)}
                          className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-md font-medium transition-colors flex items-center space-x-1"
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <Trash2 className="h-4 w-4" />
                          <span>Suppr.</span>
                        </motion.button>
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap gap-2">
                      <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full font-medium">
                        localStorage
                      </span>
                      {modelData.metadata?.trained && (
                        <span className="px-2 py-1 bg-primary-500/20 text-primary-400 text-xs rounded-full font-medium">
                          Entraîné
                        </span>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        </div>

        {/* Instructions d'utilisation */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-8 card p-6 bg-primary-500/5 border border-primary-500/20"
        >
          <div className="flex items-start space-x-4">
            <div className="p-3 bg-primary-500/20 rounded-lg">
              <Info className="h-6 w-6 text-primary-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-white mb-4">
                Comment utiliser mes modèles
              </h3>
              <div className="space-y-4 text-sm">
                <div className="p-4 bg-space-700/30 rounded-lg border border-space-600">
                  <div className="flex items-start space-x-2">
                    <div className="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-white">1</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-white mb-1">Sauvegarder un modèle</h4>
                      <p className="text-space-300">
                        Après avoir entraîné un modèle sur un dataset, vous pouvez le télécharger et le sauvegarder localement.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-space-700/30 rounded-lg border border-space-600">
                  <div className="flex items-start space-x-2">
                    <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-white">2</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-white mb-1">Réutiliser un modèle</h4>
                      <p className="text-space-300">
                        Dans la page d'analyse, choisissez "Modèle sauvegardé" et sélectionnez un modèle localStorage pour analyser de nouveaux datasets sans réentraîner.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-space-700/30 rounded-lg border border-space-600">
                  <div className="flex items-start space-x-2">
                    <div className="w-6 h-6 bg-amber-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-white">3</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-white mb-1">Synchronisation</h4>
                      <p className="text-space-300">
                        Vous pouvez uploader vos modèles localStorage vers le serveur pour les partager entre différentes sessions.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    );
}
