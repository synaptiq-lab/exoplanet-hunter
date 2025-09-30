export interface PredictionResult {
  classification: 'CONFIRMED' | 'CANDIDATE' | 'FALSE POSITIVE';
  confidence_score: number;
  features_importance: Record<string, number>;
  explanation: string;
}

export interface ModelStats {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  training_samples: number;
  last_trained: string;
}

export interface TrainingConfig {
  algorithm: 'random_forest' | 'neural_network' | 'svm' | 'gradient_boosting';
  test_size: number;
  random_state: number;
  hyperparameters: Record<string, any>;
}

export interface DatasetInfo {
  name: string;
  description: string;
  samples: number;
  confirmed_planets: number;
  candidates: number;
  false_positives: number;
}

export interface ExoplanetData {
  koi_period: number;
  koi_duration: number;
  koi_depth: number;
  koi_prad: number;
  koi_srad?: number;
  koi_stemp?: number;
  koi_smass?: number;
}

export interface AnalysisResult {
  predictions: PredictionResult[];
  total_samples: number;
  processing_time: string;
}

export interface TrainingResult {
  message: string;
  new_stats: ModelStats;
  training_config: TrainingConfig;
  samples_used: number;
}

export interface UploadStatus {
  status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
  progress: number;
  message: string;
}



