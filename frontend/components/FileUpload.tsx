'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { UploadStatus } from '@/types';
import { apiClient } from '@/lib/api';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onFileRemove: () => void;
  accept?: Record<string, string[]>;
  maxSize?: number;
  uploadStatus: UploadStatus;
  className?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  onFileRemove,
  accept = { 'text/csv': ['.csv'] },
  maxSize = 10 * 1024 * 1024, // 10MB
  uploadStatus,
  className
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string>('');

  const onDrop = useCallback(async (acceptedFiles: File[], rejectedFiles: any[]) => {
    setValidationError('');
    
    if (rejectedFiles.length > 0) {
      const error = rejectedFiles[0].errors[0];
      if (error.code === 'file-too-large') {
        setValidationError('Le fichier est trop volumineux (max 10MB)');
      } else if (error.code === 'file-invalid-type') {
        setValidationError('Seuls les fichiers CSV sont acceptés');
      } else {
        setValidationError('Erreur lors du téléchargement du fichier');
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      
      // Validation du CSV avant de continuer
      try {
        const validation = await apiClient.validateCSV(file);
        
        if (!validation.isValid) {
          setValidationError(validation.errors.join('. '));
          return;
        }
        
        setSelectedFile(file);
        onFileSelect(file);
      } catch (error) {
        setValidationError('Erreur lors de la validation du fichier CSV');
      }
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
    disabled: uploadStatus.status === 'uploading' || uploadStatus.status === 'processing'
  });

  const removeFile = () => {
    setSelectedFile(null);
    setValidationError('');
    onFileRemove();
  };

  const getStatusIcon = () => {
    switch (uploadStatus.status) {
      case 'uploading':
      case 'processing':
        return <Loader2 className="h-5 w-5 animate-spin" />;
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-400" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-400" />;
      default:
        return <Upload className="h-8 w-8" />;
    }
  };

  const getStatusColor = () => {
    switch (uploadStatus.status) {
      case 'success':
        return 'border-green-500 bg-green-500/10';
      case 'error':
        return 'border-red-500 bg-red-500/10';
      case 'uploading':
      case 'processing':
        return 'border-primary-500 bg-primary-500/10';
      default:
        return isDragActive ? 'border-primary-500 bg-primary-500/10' : 'border-space-600';
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      <div
        {...getRootProps()}
        className={cn(
          "relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300",
          getStatusColor(),
          uploadStatus.status === 'uploading' || uploadStatus.status === 'processing' 
            ? 'cursor-not-allowed opacity-50' 
            : 'hover:border-primary-400 hover:bg-primary-500/5'
        )}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-4">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 200 }}
          >
            {getStatusIcon()}
          </motion.div>
          
          <div>
            {uploadStatus.status === 'idle' && !selectedFile && (
              <>
                <h3 className="text-lg font-medium text-white mb-2">
                  {isDragActive ? 'Déposez le fichier ici' : 'Téléchargez vos données CSV'}
                </h3>
                <p className="text-space-400 text-sm">
                  Glissez-déposez un fichier CSV ou cliquez pour sélectionner
                </p>
                <p className="text-space-500 text-xs mt-2">
                  Formats supportés: CSV • Taille max: 10MB
                </p>
              </>
            )}
            
            {uploadStatus.status === 'uploading' && (
              <>
                <h3 className="text-lg font-medium text-white mb-2">
                  Téléchargement en cours...
                </h3>
                <div className="w-full bg-space-700 rounded-full h-2 mb-2">
                  <motion.div
                    className="bg-primary-500 h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${uploadStatus.progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
                <p className="text-space-400 text-sm">{uploadStatus.progress}%</p>
              </>
            )}
            
            {uploadStatus.status === 'processing' && (
              <>
                <h3 className="text-lg font-medium text-white mb-2">
                  Analyse en cours...
                </h3>
                <p className="text-space-400 text-sm">
                  Le modèle IA analyse vos données
                </p>
              </>
            )}
            
            {uploadStatus.status === 'success' && (
              <>
                <h3 className="text-lg font-medium text-green-400 mb-2">
                  Analyse terminée avec succès!
                </h3>
                <p className="text-space-400 text-sm">
                  {uploadStatus.message}
                </p>
              </>
            )}
            
            {uploadStatus.status === 'error' && (
              <>
                <h3 className="text-lg font-medium text-red-400 mb-2">
                  Erreur lors de l'analyse
                </h3>
                <p className="text-space-400 text-sm">
                  {uploadStatus.message}
                </p>
              </>
            )}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {selectedFile && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="card flex items-center justify-between p-4"
          >
            <div className="flex items-center space-x-3">
              <File className="h-5 w-5 text-primary-400" />
              <div>
                <p className="text-white font-medium">{selectedFile.name}</p>
                <p className="text-space-400 text-sm">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            
            <motion.button
              onClick={removeFile}
              className="p-2 text-space-400 hover:text-red-400 transition-colors rounded-full hover:bg-red-500/10"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              disabled={uploadStatus.status === 'uploading' || uploadStatus.status === 'processing'}
            >
              <X className="h-4 w-4" />
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {validationError && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-center space-x-2 p-3 bg-red-500/10 border border-red-500/50 rounded-lg"
          >
            <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
            <p className="text-red-400 text-sm">{validationError}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default FileUpload;

