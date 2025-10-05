import axios from 'axios';
import { 
  ModelStats, 
  AnalysisResult, 
  TrainingResult, 
  TrainingConfig, 
  ExoplanetData, 
  PredictionResult,
  DatasetInfo 
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteurs pour gestion d'erreurs
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    }
    throw error;
  }
);

// Export des types ExoMiner
export interface ExoMinerJob {
  job_id: string;
  filename: string;
  status: 'created' | 'running' | 'completed' | 'failed';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds: number;
  progress: number;
  info?: any;
}

export interface ExoMinerResults {
  job_id: string;
  status: string;
  filename: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds: number;
  progress: number;
  results: {
    summary: {
      total_tics_processed: number;
      high_confidence_candidates: number;
      avg_score?: number;
    };
    exominer_catalog?: {
      total_objects: number;
      unique_stars: number;
      high_confidence_candidates?: number;
      average_score?: number;
      columns: string[];
      sample_data: any[];
    };
    files: Array<{
      name: string;
      path: string;
      size_mb: number;
    }>;
    total_files: number;
  };
}

export interface ExoMinerAnalysisParams {
  data_collection_mode?: string;
  num_processes?: number;
  num_jobs?: number;
  download_spoc_data_products?: boolean;
  stellar_parameters_source?: string;
  ruwe_source?: string;
  exominer_model?: string;
}

export const apiClient = {
  // Vérification de santé
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await api.get('/health');
    return response.data;
  },

  // Statistiques du modèle
  async getModelStats(): Promise<ModelStats> {
    const response = await api.get('/model/stats');
    return response.data;
  },

  // Prédiction par fichier CSV
  async predictFromFile(file: File): Promise<AnalysisResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/predict', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  // Analyse d'un seul objet
  async analyzeSingleTarget(data: ExoplanetData): Promise<PredictionResult> {
    const response = await api.post('/analyze/single', data);
    return response.data;
  },

  // Réentraînement du modèle
  async retrainModel(file: File, config: TrainingConfig): Promise<TrainingResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('config', JSON.stringify(config));
    
    const response = await api.post('/train', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  // Informations sur les datasets
  async getDatasetsInfo(): Promise<{
    available_datasets: DatasetInfo[];
    key_features: string[];
  }> {
    const response = await api.get('/datasets/info');
    return response.data;
  },

  // === Nouvelles méthodes pour la gestion des modèles localStorage ===
  
  // Lister les modèles disponibles sur le serveur
  async listLocalStorageModels(): Promise<{ available_models: Array<{
    format_type: string;
    filename: string;
    available: boolean;
    last_modified: string | null;
  }>; message: string }> {
    const response = await api.get('/models/localStorage/list');
    return response.data;
  },

  // Télécharger un modèle pour localStorage
  async downloadModelForLocalStorage(formatType: string): Promise<{
    model_json: any;
    metadata: {
      format_type: string;
      trained: boolean;
      feature_columns: string[];
      label_encoder_classes: string[];
    };
    format_type: string;
    message: string;
  }> {
    const response = await api.get(`/models/localStorage/download/${formatType}`);
    return response.data;
  },

  // Uploader un modèle depuis localStorage vers le serveur
  async uploadModelFromLocalStorage(modelData: {
    format_type: string;
    model_json: any;
  }): Promise<{
    message: string;
    format_type: string;
    model_file: string;
  }> {
    const response = await api.post('/models/localStorage/upload', modelData);
    return response.data;
  },

  // Charger un modèle depuis localStorage dans le pipeline ML
  async loadModelFromLocalStorage(formatType: string, modelData: {
    model_json: any;
    feature_columns: string[];
  }): Promise<{
    message: string;
    format_type: string;
    trained: boolean;
    feature_count: number;
  }> {
    const response = await api.post(`/models/localStorage/load/${formatType}`, modelData);
    return response.data;
  },

  // Analyser avec un modèle sauvegardé
  async analyzeWithModel(file: File, formatType: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('format_type', formatType);
    
    const response = await api.post('/analyze/withModel', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  // === ExoMiner API (Version Jobs) ===
  
  // Analyser avec ExoMiner (workflow complet)
  async analyzeWithExoMiner(
    file: File,
    params: {
      data_collection_mode?: string;
      num_processes?: number;
      num_jobs?: number;
      download_spoc_data_products?: boolean;
      stellar_parameters_source?: string;
      ruwe_source?: string;
      exominer_model?: string;
    }
  ): Promise<{
    success: boolean;
    message: string;
    job_id: string;
    logs: string[];
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('data_collection_mode', params.data_collection_mode || '2min');
    formData.append('num_processes', (params.num_processes || 2).toString());
    formData.append('num_jobs', (params.num_jobs || 1).toString());
    formData.append('download_spoc_data_products', (params.download_spoc_data_products !== false).toString());
    formData.append('stellar_parameters_source', params.stellar_parameters_source || 'ticv8');
    formData.append('ruwe_source', params.ruwe_source || 'gaiadr2');
    formData.append('exominer_model', params.exominer_model || 'exominer++_single');
    
    const response = await api.post('/exominer/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 900000, // 15 minutes
    });
    
    return response.data;
  },

  // Lister tous les jobs ExoMiner
  async listExoMinerJobs(): Promise<{
    jobs: Record<string, {
      job_id: string;
      filename: string;
      status: string;
      created_at: string;
      started_at?: string;
      completed_at?: string;
      duration_seconds: number;
      progress: number;
      info?: any;
    }>;
    total: number;
  }> {
    const response = await api.get('/exominer/jobs');
    return response.data;
  },

  // Obtenir le statut d'un job
  async getExoMinerJobStatus(jobId: string): Promise<{
    job_id: string;
    filename: string;
    status: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    duration_seconds: number;
    progress: number;
    info?: any;
  }> {
    const response = await api.get(`/exominer/jobs/${jobId}/status`);
    return response.data;
  },

  // Obtenir les résultats d'un job
  async getExoMinerJobResults(jobId: string): Promise<{
    job_id: string;
    status: string;
    filename: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    duration_seconds: number;
    progress: number;
    results: {
      summary: {
        total_tics_processed: number;
        high_confidence_candidates: number;
        avg_score?: number;
      };
      exominer_catalog?: {
        total_objects: number;
        unique_stars: number;
        high_confidence_candidates?: number;
        average_score?: number;
        columns: string[];
        sample_data: any[];
      };
      files: Array<{
        name: string;
        path: string;
        size_mb: number;
      }>;
      total_files: number;
    };
  }> {
    const response = await api.get(`/exominer/jobs/${jobId}/results`);
    return response.data;
  },

  // Télécharger les résultats d'un job
  async downloadExoMinerResults(jobId: string): Promise<Blob> {
    const response = await api.get(`/exominer/jobs/${jobId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Supprimer un job
  async deleteExoMinerJob(jobId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await api.delete(`/exominer/jobs/${jobId}`);
    return response.data;
  },

  // Nettoyer les jobs anciens
  async cleanupExoMinerJobs(): Promise<{
    success: boolean;
    message: string;
    deleted_count: number;
  }> {
    const response = await api.post('/exominer/jobs/cleanup');
    return response.data;
  },

  // Vérifier l'état du système ExoMiner
  async exominerHealth(): Promise<{
    docker: {
      available: boolean;
      message: string;
    };
    exominer_image: {
      available: boolean;
      message: string;
    };
    status: string;
  }> {
    const response = await api.get('/exominer/health');
    return response.data;
  },

  // Télécharger l'image Docker ExoMiner
  async exominerPullImage(): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await api.post('/exominer/image/pull');
    return response.data;
  },

  // Upload CSV TIC IDs
  async exominerUpload(file: File): Promise<{
    success: boolean;
    message: string;
    analysis_id: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/exominer/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  // Lancer une analyse ExoMiner
  async exominerRunAnalysis(
    analysisId: string,
    params: {
      data_collection_mode: string;
      num_processes: number;
      num_jobs: number;
      model: string;
    }
  ): Promise<{
    success: boolean;
    message: string;
    analysis_id: string;
    logs: string[];
  }> {
    const formData = new FormData();
    formData.append('data_collection_mode', params.data_collection_mode);
    formData.append('num_processes', params.num_processes.toString());
    formData.append('num_jobs', params.num_jobs.toString());
    formData.append('model', params.model);
    
    const response = await api.post(`/exominer/${analysisId}/run`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 900000, // 15 minutes
    });
    
    return response.data;
  },

  // Lister toutes les analyses
  async exominerListAnalyses(): Promise<{
    analyses: Array<{
      analysis_id: string;
      filename: string;
      created_at: string;
      status: string;
      info?: any;
    }>;
    total: number;
  }> {
    const response = await api.get('/exominer/analyses');
    return response.data;
  },

  // Obtenir le statut d'une analyse
  async exominerGetStatus(analysisId: string): Promise<{
    analysis_id: string;
    status: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    filename: string;
    info: any;
  }> {
    const response = await api.get(`/exominer/${analysisId}/status`);
    return response.data;
  },

  // Récupérer les résultats d'une analyse
  async exominerGetResults(analysisId: string): Promise<any> {
    const response = await api.get(`/exominer/${analysisId}/results`);
    return response.data;
  },

  // Supprimer une analyse
  async exominerDeleteAnalysis(analysisId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await api.delete(`/exominer/${analysisId}`);
    return response.data;
  },

  // Validation de fichier CSV flexible (supporte Kepler, K2, TESS)
  async validateCSV(file: File): Promise<{
    isValid: boolean;
    headers: string[];
    rowCount: number;
    errors: string[];
    detectedFormat?: string;
  }> {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const text = e.target?.result as string;
          
          // Filtrer les lignes de commentaires (commencent par #)
          const lines = text.split('\n')
            .filter(line => line.trim() && !line.trim().startsWith('#'));
          
          if (lines.length < 2) {
            resolve({
              isValid: false,
              headers: [],
              rowCount: 0,
              errors: ['Le fichier doit contenir au moins un en-tête et une ligne de données']
            });
            return;
          }

          const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
          const errors: string[] = [];
          
          // Détection automatique du format basé sur les 3 formats officiels NASA
          let detectedFormat = 'unknown';
          let hasRequiredColumns = false;
          let formatDescription = '';
          
          // Format KEPLER (KOI) : Kepler Objects of Interest
          // Colonne cible: koi_pdisposition ou koi_disposition
          if (headers.includes('kepoi_name') && (headers.includes('koi_pdisposition') || headers.includes('koi_disposition'))) {
            detectedFormat = 'kepler_koi';
            formatDescription = 'Kepler Objects of Interest (KOI)';
            const keplerRequired = ['kepoi_name', 'koi_period'];
            hasRequiredColumns = keplerRequired.every(col => headers.includes(col));
          }
          // Format TESS (TOI) : TESS Objects of Interest
          // Colonne cible: tfopwg_disp (CP/FP/PC/KP)
          else if (headers.includes('toi') && headers.includes('tfopwg_disp')) {
            detectedFormat = 'tess_toi';
            formatDescription = 'TESS Objects of Interest (TOI)';
            const tessRequired = ['toi', 'tfopwg_disp', 'pl_orbper'];
            hasRequiredColumns = tessRequired.every(col => headers.includes(col));
          }
          // Format K2 : K2 Planets and Candidates
          // Colonne cible: disposition
          else if (headers.includes('pl_name') && headers.includes('disposition') && headers.includes('pl_orbper')) {
            detectedFormat = 'k2';
            formatDescription = 'K2 Planets and Candidates';
            const k2Required = ['pl_name', 'disposition', 'pl_orbper'];
            hasRequiredColumns = k2Required.every(col => headers.includes(col));
          }

          if (!hasRequiredColumns) {
            errors.push(`Format non reconnu. Formats officiels supportés:`);
            errors.push(`• Kepler (KOI): kepoi_name + koi_pdisposition/koi_disposition + koi_period`);
            errors.push(`• TESS (TOI): toi + tfopwg_disp + pl_orbper`);
            errors.push(`• K2: pl_name + disposition + pl_orbper`);
          }

          // Validation de la cohérence des lignes (seulement si pas d'erreurs de format)
          if (hasRequiredColumns) {
            const headerCount = headers.length;
            const inconsistentLines: number[] = [];
            
            for (let i = 1; i < Math.min(lines.length, 50); i++) { // Vérifier les 50 premières lignes
              const fields = lines[i].split(',').length;
              if (fields !== headerCount) {
                inconsistentLines.push(i + 1);
              }
            }

            if (inconsistentLines.length > 5) { // Tolérer quelques lignes incohérentes
              errors.push(`Trop de lignes avec nombre de champs incorrect: ${inconsistentLines.slice(0, 5).join(', ')}...`);
              errors.push('Vérifiez que toutes les lignes ont le même nombre de colonnes');
            }
          }

          resolve({
            isValid: errors.length === 0,
            headers,
            rowCount: lines.length - 1,
            errors,
            detectedFormat
          });
        } catch (error) {
          resolve({
            isValid: false,
            headers: [],
            rowCount: 0,
            errors: ['Erreur lors de la lecture du fichier CSV'],
            detectedFormat: 'error'
          });
        }
      };
      reader.readAsText(file);
    });
  }
};

// Export des fonctions ExoMiner pour la page
export const {
  analyzeWithExoMiner,
  listExoMinerJobs,
  getExoMinerJobStatus,
  getExoMinerJobResults,
  downloadExoMinerResults,
  deleteExoMinerJob,
  cleanupExoMinerJobs
} = apiClient;

export default apiClient;


