'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { 
  Upload, 
  Play, 
  Download, 
  Trash2, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  Clock,
  FileText,
  BarChart3,
  Settings,
  AlertCircle
} from 'lucide-react';
import { 
  analyzeWithExoMiner, 
  listExoMinerJobs, 
  getExoMinerJobStatus, 
  getExoMinerJobResults,
  downloadExoMinerResults,
  deleteExoMinerJob,
  cleanupExoMinerJobs,
  ExoMinerJob,
  ExoMinerResults,
  ExoMinerAnalysisParams
} from '@/lib/api';
import DashboardLayout from '@/components/dashboard/DashboardLayout';

interface ExoMinerPageProps {}

const ExoMinerPage: React.FC<ExoMinerPageProps> = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [jobs, setJobs] = useState<Record<string, ExoMinerJob>>({});
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [jobResults, setJobResults] = useState<ExoMinerResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  
  // Paramètres ExoMiner
  const [params, setParams] = useState<ExoMinerAnalysisParams>({
    data_collection_mode: '2min',
    num_processes: 2,
    num_jobs: 1,
    download_spoc_data_products: true,
    stellar_parameters_source: 'ticv8',
    ruwe_source: 'gaiadr2',
    exominer_model: 'exominer++_single'
  });

  // Charger les jobs au montage
  useEffect(() => {
    loadJobs();
  }, []);

  // Polling pour les jobs en cours
  useEffect(() => {
    const interval = setInterval(() => {
      const runningJobs = Object.values(jobs).filter(job => job.status === 'running');
      if (runningJobs.length > 0) {
        loadJobs();
      }
    }, 5000); // Vérifier toutes les 5 secondes

    return () => clearInterval(interval);
  }, [jobs]);

  const loadJobs = useCallback(async () => {
    try {
      const response = await listExoMinerJobs();
      setJobs(response.jobs);
    } catch (err) {
      console.error('Erreur chargement jobs:', err);
    }
  }, []);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.csv')) {
        setError('Le fichier doit être un CSV');
        return;
      }
      setUploadedFile(file);
      setError(null);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.name.endsWith('.csv')) {
      setUploadedFile(file);
      setError(null);
    } else {
      setError('Le fichier doit être un CSV');
    }
  };

  const handleAnalyze = async () => {
    if (!uploadedFile) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const result = await analyzeWithExoMiner(uploadedFile, params);
      
      if (result.success) {
        setSelectedJob(result.job_id);
        await loadJobs();
      } else {
        setError('Échec du lancement de l\'analyse ExoMiner');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de l\'analyse');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleJobSelect = async (jobId: string) => {
    setSelectedJob(jobId);
    
    try {
      const job = jobs[jobId];
      if (job.status === 'completed') {
        const results = await getExoMinerJobResults(jobId);
        setJobResults(results);
      } else {
        setJobResults(null);
      }
    } catch (err) {
      console.error('Erreur chargement résultats:', err);
    }
  };

  const handleDownloadResults = async (jobId: string) => {
    try {
      const blob = await downloadExoMinerResults(jobId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `exominer_results_${jobId}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Erreur lors du téléchargement');
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    try {
      await deleteExoMinerJob(jobId);
      await loadJobs();
      if (selectedJob === jobId) {
        setSelectedJob(null);
        setJobResults(null);
      }
    } catch (err) {
      setError('Erreur lors de la suppression');
    }
  };

  const handleCleanup = async () => {
    try {
      await cleanupExoMinerJobs();
      await loadJobs();
    } catch (err) {
      setError('Erreur lors du nettoyage');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-400" />;
      case 'running':
        return <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-2">
            ExoMiner NASA Pipeline
          </h1>
          <p className="text-space-300">
            Analysez vos TIC IDs avec le pipeline professionnel de la NASA
          </p>
        </motion.div>

        {/* Error Alert */}
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-6 bg-red-500/10 border border-red-500/20 rounded-lg p-4"
          >
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
              <span className="text-red-400">{error}</span>
            </div>
          </motion.div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Upload Section */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-1"
          >
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-white">Upload CSV</h2>
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="p-2 text-space-400 hover:text-white transition-colors"
                >
                  <Settings className="w-5 h-5" />
                </button>
              </div>

              {/* Settings Panel */}
              {showSettings && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mb-4 p-4 bg-space-700/30 rounded-lg"
                >
                  <h3 className="text-sm font-medium text-white mb-3">Paramètres ExoMiner</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-space-400">Mode de collecte</label>
                      <select
                        value={params.data_collection_mode}
                        onChange={(e) => setParams({...params, data_collection_mode: e.target.value})}
                        className="w-full mt-1 px-3 py-2 bg-space-700 border border-space-600 rounded text-white text-sm"
                      >
                        <option value="2min">2min</option>
                        <option value="FFI">FFI</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-space-400">Processus</label>
                      <input
                        type="number"
                        min="1"
                        max="8"
                        value={params.num_processes}
                        onChange={(e) => setParams({...params, num_processes: parseInt(e.target.value)})}
                        className="w-full mt-1 px-3 py-2 bg-space-700 border border-space-600 rounded text-white text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-space-400">Modèle</label>
                      <select
                        value={params.exominer_model}
                        onChange={(e) => setParams({...params, exominer_model: e.target.value})}
                        className="w-full mt-1 px-3 py-2 bg-space-700 border border-space-600 rounded text-white text-sm"
                      >
                        <option value="exominer++_single">ExoMiner++ Single</option>
                        <option value="exominer++_cviter-mean-ensemble">CV Iter Mean Ensemble</option>
                        <option value="exominer++_cv-super-mean-ensemble">CV Super Mean Ensemble</option>
                      </select>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* File Upload */}
              <div
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                className="border-2 border-dashed border-space-600 rounded-lg p-8 text-center hover:border-space-500 transition-colors"
              >
                <Upload className="w-12 h-12 text-space-400 mx-auto mb-4" />
                <p className="text-space-300 mb-2">Glissez votre fichier CSV ici</p>
                <p className="text-space-400 text-sm mb-4">ou</p>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="csv-upload"
                />
                <label
                  htmlFor="csv-upload"
                  className="btn-primary cursor-pointer"
                >
                  Sélectionner un fichier
                </label>
              </div>

              {uploadedFile && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 p-3 bg-space-700/30 rounded-lg"
                >
                  <div className="flex items-center">
                    <FileText className="w-5 h-5 text-primary-400 mr-2" />
                    <span className="text-white text-sm">{uploadedFile.name}</span>
                  </div>
                </motion.div>
              )}

              <button
                onClick={handleAnalyze}
                disabled={!uploadedFile || isAnalyzing}
                className="w-full mt-4 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Lancement...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Lancer ExoMiner
                  </>
                )}
              </button>
            </div>
          </motion.div>

          {/* Jobs List */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="lg:col-span-2"
          >
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-white">Jobs ExoMiner</h2>
                <button
                  onClick={handleCleanup}
                  className="text-space-400 hover:text-white transition-colors"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>

              {Object.keys(jobs).length === 0 ? (
                <div className="text-center py-8 text-space-400">
                  <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Aucun job ExoMiner</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {Object.entries(jobs).map(([jobId, job]) => (
                    <motion.div
                      key={jobId}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`p-4 rounded-lg border cursor-pointer transition-all ${
                        selectedJob === jobId
                          ? 'bg-primary-500/10 border-primary-500/30'
                          : 'bg-space-700/30 border-space-600 hover:border-space-500'
                      }`}
                      onClick={() => handleJobSelect(jobId)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          {getStatusIcon(job.status)}
                          <div>
                            <p className="text-white font-medium">{job.filename}</p>
                            <p className="text-space-400 text-sm">
                              {formatDuration(job.duration_seconds)} • {job.status}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {job.status === 'completed' && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDownloadResults(jobId);
                              }}
                              className="p-2 text-space-400 hover:text-white transition-colors"
                            >
                              <Download className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteJob(jobId);
                            }}
                            className="p-2 text-space-400 hover:text-red-400 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      
                      {job.status === 'running' && (
                        <div className="mt-3">
                          <div className="w-full bg-space-700 rounded-full h-2">
                            <div 
                              className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${job.progress}%` }}
                            />
                          </div>
                          <p className="text-space-400 text-xs mt-1">
                            Progression: {job.progress}%
                          </p>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Results Section */}
        {jobResults && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6"
          >
            <div className="card">
              <h2 className="text-xl font-semibold text-white mb-4">Résultats ExoMiner</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-space-700/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-primary-400">
                    {jobResults.results.summary.total_tics_processed}
                  </div>
                  <div className="text-space-400 text-sm">TICs analysés</div>
                </div>
                <div className="bg-space-700/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-primary-400">
                    {jobResults.results.summary.high_confidence_candidates || 0}
                  </div>
                  <div className="text-space-400 text-sm">Haute confiance</div>
                </div>
                <div className="bg-space-700/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-primary-400">
                    {jobResults.results.summary.avg_score?.toFixed(3) || 'N/A'}
                  </div>
                  <div className="text-space-400 text-sm">Score moyen</div>
                </div>
              </div>

              {jobResults.results.exominer_catalog && (
                <div className="bg-space-700/30 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-white mb-3">Catalogue ExoMiner</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-space-600">
                          {jobResults.results.exominer_catalog.columns.slice(0, 5).map((col) => (
                            <th key={col} className="text-left py-2 text-space-400">{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {jobResults.results.exominer_catalog.sample_data.slice(0, 5).map((row, idx) => (
                          <tr key={idx} className="border-b border-space-700">
                            {jobResults.results.exominer_catalog.columns.slice(0, 5).map((col) => (
                              <td key={col} className="py-2 text-space-300">
                                {row[col]}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default ExoMinerPage;
