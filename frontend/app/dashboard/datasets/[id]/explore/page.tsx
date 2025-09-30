'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  Database, 
  BarChart3, 
  Table, 
  PieChart,
  Loader2,
  Download,
  Filter,
  Search,
  Eye,
  Info
} from 'lucide-react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';

interface ExploreData {
  metadata: {
    id: string;
    filename: string;
    upload_date: string;
    rows: number;
    columns: number;
    has_labels: boolean;
  };
  statistics: {[key: string]: {
    mean: number;
    std: number;
    min: number;
    max: number;
    null_count: number;
  }};
  sample_data: any[];
  class_distribution: {[key: string]: number};
  column_info: string[];
}

const ExplorePage = () => {
  const params = useParams();
  const router = useRouter();
  const datasetId = params.id as string;
  
  const [data, setData] = useState<ExploreData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'data' | 'stats' | 'distribution'>('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);

  useEffect(() => {
    loadExploreData();
  }, [datasetId]);

  const loadExploreData = async () => {
    try {
      const response = await fetch(`http://localhost:8000/datasets/${datasetId}/explore`);
      if (!response.ok) {
        throw new Error('Dataset non trouvé');
      }
      const result = await response.json();
      setData(result);
      setSelectedColumns(result.column_info.slice(0, 5)); // Afficher les 5 premières colonnes par défaut
    } catch (error) {
      console.error('Erreur lors du chargement:', error);
      alert('Erreur lors du chargement du dataset');
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const filteredSampleData = data?.sample_data.filter(row => 
    Object.values(row).some(value => 
      String(value).toLowerCase().includes(searchTerm.toLowerCase())
    )
  ) || [];

  const filteredColumns = data?.column_info.filter(col =>
    col.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      </DashboardLayout>
    );
  }

  if (!data) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <Database className="h-16 w-16 text-space-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Dataset non trouvé</h3>
        </div>
      </DashboardLayout>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Vue d\'ensemble', icon: Info },
    { id: 'data', label: 'Données', icon: Table },
    { id: 'stats', label: 'Statistiques', icon: BarChart3 },
    { id: 'distribution', label: 'Distribution', icon: PieChart }
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <motion.button
              onClick={() => router.back()}
              className="p-2 bg-space-700 hover:bg-space-600 text-space-300 hover:text-white rounded-lg transition-colors"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <ArrowLeft className="h-5 w-5" />
            </motion.button>
            
            <div>
              <h1 className="text-2xl font-bold text-white">
                Exploration : {data.metadata.filename}
              </h1>
              <p className="text-space-400">
                {data.metadata.rows.toLocaleString()} lignes • {data.metadata.columns} colonnes
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              data.metadata.has_labels 
                ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                : 'bg-gray-500/20 text-gray-400 border border-gray-500/50'
            }`}>
              {data.metadata.has_labels ? 'Avec Labels' : 'Sans Labels'}
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-space-800/30 p-1 rounded-xl">
          {tabs.map((tab) => (
            <motion.button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-primary-600 text-white shadow-lg'
                  : 'text-space-300 hover:text-white hover:bg-space-700'
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </motion.button>
          ))}
        </div>

        {/* Content */}
        <div className="min-h-96">
          {activeTab === 'overview' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              {/* Metadata Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-2">
                    <Database className="h-6 w-6 text-blue-400" />
                    <span className="text-2xl font-bold text-white">{data.metadata.rows.toLocaleString()}</span>
                  </div>
                  <p className="text-space-400">Lignes de données</p>
                </div>
                
                <div className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-2">
                    <Table className="h-6 w-6 text-green-400" />
                    <span className="text-2xl font-bold text-white">{data.metadata.columns}</span>
                  </div>
                  <p className="text-space-400">Colonnes</p>
                </div>
                
                <div className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-2">
                    <BarChart3 className="h-6 w-6 text-purple-400" />
                    <span className="text-2xl font-bold text-white">{Object.keys(data.statistics).length}</span>
                  </div>
                  <p className="text-space-400">Colonnes numériques</p>
                </div>
                
                <div className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-2">
                    <PieChart className="h-6 w-6 text-yellow-400" />
                    <span className="text-2xl font-bold text-white">
                      {Object.keys(data.class_distribution).length || 0}
                    </span>
                  </div>
                  <p className="text-space-400">Classes</p>
                </div>
              </div>

              {/* Column Info */}
              <div className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6">
                <h3 className="text-xl font-semibold text-white mb-4">Colonnes disponibles</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                  {data.column_info.map((column, index) => (
                    <div key={index} className="flex items-center space-x-2 p-2 bg-space-700/30 rounded-lg">
                      <div className="w-2 h-2 bg-primary-400 rounded-full"></div>
                      <span className="text-space-300 text-sm font-mono">{column}</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'data' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              {/* Search and Filter */}
              <div className="flex items-center space-x-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-space-400" />
                  <input
                    type="text"
                    placeholder="Rechercher dans les données..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-space-700/50 border border-space-600 rounded-lg text-white placeholder-space-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                
                <div className="text-space-400 text-sm">
                  {filteredSampleData.length} / {data.sample_data.length} lignes
                </div>
              </div>

              {/* Data Table */}
              <div className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-space-700/50">
                      <tr>
                        {selectedColumns.map((column) => (
                          <th key={column} className="px-4 py-3 text-left text-space-300 font-medium text-sm">
                            {column}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {filteredSampleData.slice(0, 50).map((row, index) => (
                        <tr key={index} className="border-t border-space-700">
                          {selectedColumns.map((column) => (
                            <td key={column} className="px-4 py-3 text-space-300 text-sm font-mono">
                              {row[column] !== null && row[column] !== undefined 
                                ? String(row[column]).substring(0, 50)
                                : '-'
                              }
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                {filteredSampleData.length > 50 && (
                  <div className="p-4 text-center text-space-400 text-sm border-t border-space-700">
                    Affichage des 50 premiers résultats sur {filteredSampleData.length}
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'stats' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {Object.entries(data.statistics).map(([column, stats]) => (
                  <div key={column} className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4 font-mono">{column}</h3>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-space-400 text-sm">Moyenne</span>
                          <span className="text-white font-mono text-sm">{stats.mean.toFixed(3)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-space-400 text-sm">Écart-type</span>
                          <span className="text-white font-mono text-sm">{stats.std.toFixed(3)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-space-400 text-sm">Minimum</span>
                          <span className="text-white font-mono text-sm">{stats.min.toFixed(3)}</span>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-space-400 text-sm">Maximum</span>
                          <span className="text-white font-mono text-sm">{stats.max.toFixed(3)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-space-400 text-sm">Valeurs nulles</span>
                          <span className="text-white font-mono text-sm">{stats.null_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-space-400 text-sm">Complétude</span>
                          <span className="text-green-400 font-mono text-sm">
                            {(((data.metadata.rows - stats.null_count) / data.metadata.rows) * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'distribution' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              {Object.keys(data.class_distribution).length > 0 ? (
                <div className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6">
                  <h3 className="text-xl font-semibold text-white mb-6">
                    Distribution des Classes (koi_disposition)
                  </h3>
                  
                  <div className="space-y-4">
                    {Object.entries(data.class_distribution).map(([className, count]) => {
                      const percentage = (count / data.metadata.rows) * 100;
                      const colors = {
                        'CONFIRMED': 'bg-green-500',
                        'CANDIDATE': 'bg-yellow-500', 
                        'FALSE POSITIVE': 'bg-red-500'
                      };
                      const color = colors[className as keyof typeof colors] || 'bg-blue-500';
                      
                      return (
                        <div key={className} className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-white font-medium">{className}</span>
                            <span className="text-space-300">
                              {count.toLocaleString()} ({percentage.toFixed(1)}%)
                            </span>
                          </div>
                          <div className="w-full bg-space-700 rounded-full h-3">
                            <motion.div
                              className={`h-3 rounded-full ${color}`}
                              initial={{ width: 0 }}
                              animate={{ width: `${percentage}%` }}
                              transition={{ duration: 1, delay: 0.2 }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-12 text-center">
                  <PieChart className="h-16 w-16 text-space-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">
                    Aucune distribution de classes
                  </h3>
                  <p className="text-space-400">
                    Ce dataset ne contient pas de colonne de classification (koi_disposition)
                  </p>
                </div>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default ExplorePage;

