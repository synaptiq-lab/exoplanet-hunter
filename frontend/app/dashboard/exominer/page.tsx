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
  analyzeWithExoMinerFromTics,
  listExoMinerJobs, 
  getExoMinerJobStatus, 
  getExoMinerJobResults,
  downloadExoMinerResults,
  deleteExoMinerJob,
  cleanupExoMinerJobs,
  ExoMinerJob,
  ExoMinerResults,
  ExoMinerAnalysisParams,
  ExoMinerPrediction
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
  const [inputMode, setInputMode] = useState<'file' | 'manual'>('file');
  const [manualTicInput, setManualTicInput] = useState('');
  const [manualSectorInput, setManualSectorInput] = useState('');
  const [autoFetchSectors, setAutoFetchSectors] = useState(true);
  
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
      setJobs(response.jobs as Record<string, ExoMinerJob>);
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
    setIsAnalyzing(true);
    setError(null);

    try {
      let result;

      if (inputMode === 'manual') {
        // Mode saisie manuelle
        if (!manualTicInput.trim()) {
          setError('Veuillez saisir au moins un TIC ID');
          setIsAnalyzing(false);
          return;
        }

        // Parser les TIC IDs
        const ticIds = manualTicInput
          .split(/[,\n\s]+/)
          .map(tic => tic.trim())
          .filter(tic => tic && !isNaN(Number(tic)))
          .map(tic => Number(tic));

        if (ticIds.length === 0) {
          setError('Aucun TIC ID valide trouvé');
          setIsAnalyzing(false);
          return;
        }

        // Parser les secteurs si fournis
        let sectors: string[] | undefined = undefined;
        if (!autoFetchSectors && manualSectorInput.trim()) {
          sectors = manualSectorInput
            .split(/[,\n\s]+/)
            .map(s => s.trim())
            .filter(s => s);

          if (sectors.length !== ticIds.length) {
            setError(`Nombre de secteurs (${sectors.length}) différent du nombre de TIC IDs (${ticIds.length})`);
            setIsAnalyzing(false);
            return;
          }
        }

        result = await analyzeWithExoMinerFromTics(ticIds, sectors, params);
      } else {
        // Mode fichier
        if (!uploadedFile) {
          setError('Veuillez sélectionner un fichier');
          setIsAnalyzing(false);
          return;
        }

        result = await analyzeWithExoMiner(uploadedFile, params);
      }
      
      if (result.success) {
        setSelectedJob(result.job_id);
        await loadJobs();
        // Réinitialiser les champs de saisie manuelle
        if (inputMode === 'manual') {
          setManualTicInput('');
          setManualSectorInput('');
        }
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
        
        // Les prédictions s'affichent maintenant directement dans le tableau
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

  const exportPredictionsCSV = () => {
    if (!jobResults?.results || !('predictions' in jobResults.results) || !jobResults.results.predictions) return;

    const predictions = jobResults.results.predictions;
    
    // Créer le contenu CSV avec toutes les prédictions
    const csvContent = [
      ['TIC ID', 'Résultat', 'Score'],
      // Planètes confirmées
      ...predictions.confirmed.map((planet: ExoMinerPrediction) => [
        planet.tic_id,
        'Confirmée',
        planet.score.toFixed(3)
      ]),
      // Candidates
      ...predictions.candidates.map((planet: ExoMinerPrediction) => [
        planet.tic_id,
        'Candidate',
        planet.score.toFixed(3)
      ]),
      // Faux positifs
      ...predictions.false_positives.map((planet: ExoMinerPrediction) => [
        planet.tic_id,
        'Faux Positif',
        planet.score.toFixed(3)
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `exominer_predictions_${selectedJob}_${new Date().getTime()}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
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
                <h2 className="text-xl font-semibold text-white">Entrée des données</h2>
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="p-2 text-space-400 hover:text-white transition-colors"
                >
                  <Settings className="w-5 h-5" />
                </button>
              </div>

              {/* Mode Selection */}
              <div className="mb-4 flex space-x-2">
                <button
                  onClick={() => setInputMode('file')}
                  className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                    inputMode === 'file'
                      ? 'bg-primary-600 text-white'
                      : 'bg-space-700 text-space-300 hover:bg-space-600'
                  }`}
                >
                  📁 Fichier CSV
                </button>
                <button
                  onClick={() => setInputMode('manual')}
                  className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                    inputMode === 'manual'
                      ? 'bg-primary-600 text-white'
                      : 'bg-space-700 text-space-300 hover:bg-space-600'
                  }`}
                >
                  ✏️ Saisie manuelle
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

              {/* Manual Input */}
              {inputMode === 'manual' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-white font-medium mb-2">
                      TIC IDs <span className="text-red-400">*</span>
                    </label>
                    <textarea
                      value={manualTicInput}
                      onChange={(e) => setManualTicInput(e.target.value)}
                      placeholder="Exemple: 12345, 67890, 11111&#10;ou un TIC par ligne"
                      className="w-full h-32 px-3 py-2 bg-space-700 border border-space-600 rounded-lg text-white placeholder-space-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500"
                    />
                    <p className="text-space-500 text-xs mt-1">
                      Séparés par virgule, espace ou nouvelle ligne
                    </p>
                  </div>

                  <div>
                    <label className="flex items-center space-x-2 mb-3">
                      <input
                        type="checkbox"
                        checked={autoFetchSectors}
                        onChange={(e) => setAutoFetchSectors(e.target.checked)}
                        className="w-4 h-4 text-primary-600 bg-space-700 border-space-600 rounded focus:ring-primary-500"
                      />
                      <span className="text-white text-sm font-medium">
                        Récupérer automatiquement les secteurs (via astroquery)
                      </span>
                    </label>

                    {!autoFetchSectors && (
                      <div>
                        <label className="block text-white font-medium mb-2">
                          Secteurs <span className="text-red-400">*</span>
                        </label>
                        <textarea
                          value={manualSectorInput}
                          onChange={(e) => setManualSectorInput(e.target.value)}
                          placeholder="Exemple: 1, 2, 3&#10;Un secteur par TIC ID, dans le même ordre"
                          className="w-full h-24 px-3 py-2 bg-space-700 border border-space-600 rounded-lg text-white placeholder-space-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500"
                        />
                        <p className="text-space-500 text-xs mt-1">
                          ⚠️ Doit correspondre à l'ordre des TIC IDs
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* File Upload */}
              {inputMode === 'file' && (
                <>
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
                </>
              )}

              <button
                onClick={handleAnalyze}
                disabled={(inputMode === 'file' && !uploadedFile) || (inputMode === 'manual' && !manualTicInput.trim()) || isAnalyzing}
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

              {/* Prédictions ExoMiner */}
              {jobResults.results && 'predictions' in jobResults.results && jobResults.results.predictions && (
                <div className="card p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-bold text-white flex items-center">
                      <CheckCircle className="h-6 w-6 text-primary-400 mr-2" />
                      Prédictions ExoMiner ({jobResults.results.predictions.total})
                    </h3>
                    <button
                      onClick={exportPredictionsCSV}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-colors flex items-center space-x-2"
                    >
                      <Download className="h-5 w-5" />
                      <span>Exporter CSV</span>
                    </button>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-space-700">
                          <th className="text-left py-3 px-4 text-space-300 font-semibold">TIC ID</th>
                          <th className="text-left py-3 px-4 text-space-300 font-semibold">Résultat</th>
                          <th className="text-left py-3 px-4 text-space-300 font-semibold">Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {/* Planètes Confirmées */}
                        {jobResults.results.predictions.confirmed.map((planet: ExoMinerPrediction, index: number) => (
                          <motion.tr
                            key={`confirmed-${planet.tic_id}`}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="border-b border-space-700/50 hover:bg-green-500/5 transition-colors"
                          >
                            <td className="py-3 px-4">
                              <div className="flex items-center space-x-2">
                                <CheckCircle className="h-4 w-4 text-green-400" />
                                <span className="font-semibold text-white">TIC {planet.tic_id}</span>
                              </div>
                            </td>
                            <td className="py-3 px-4">
                              <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-sm font-medium">
                                Confirmée
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <span className="text-green-400 font-bold">
                                {planet.score.toFixed(3)}
                              </span>
                            </td>
                          </motion.tr>
                        ))}
                        
                        {/* Candidates */}
                        {jobResults.results.predictions.candidates.map((planet: ExoMinerPrediction, index: number) => (
                          <motion.tr
                            key={`candidate-${planet.tic_id}`}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: ((jobResults.results.predictions?.confirmed.length || 0) + index) * 0.05 }}
                            className="border-b border-space-700/50 hover:bg-yellow-500/5 transition-colors"
                          >
                            <td className="py-3 px-4">
                              <div className="flex items-center space-x-2">
                                <Clock className="h-4 w-4 text-yellow-400" />
                                <span className="font-semibold text-white">TIC {planet.tic_id}</span>
                              </div>
                            </td>
                            <td className="py-3 px-4">
                              <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-sm font-medium">
                                Candidate
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <span className="text-yellow-400 font-bold">
                                {planet.score.toFixed(3)}
                              </span>
                            </td>
                          </motion.tr>
                        ))}
                        
                        {/* Faux Positifs */}
                        {jobResults.results.predictions.false_positives.map((planet: ExoMinerPrediction, index: number) => (
                          <motion.tr
                            key={`false-positive-${planet.tic_id}`}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: ((jobResults.results.predictions?.confirmed.length || 0) + (jobResults.results.predictions?.candidates.length || 0) + index) * 0.05 }}
                            className="border-b border-space-700/50 hover:bg-red-500/5 transition-colors"
                          >
                            <td className="py-3 px-4">
                              <div className="flex items-center space-x-2">
                                <XCircle className="h-4 w-4 text-red-400" />
                                <span className="font-semibold text-white">TIC {planet.tic_id}</span>
                              </div>
                            </td>
                            <td className="py-3 px-4">
                              <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-sm font-medium">
                                Faux Positif
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <span className="text-red-400 font-bold">
                                {planet.score.toFixed(3)}
                              </span>
                            </td>
                          </motion.tr>
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