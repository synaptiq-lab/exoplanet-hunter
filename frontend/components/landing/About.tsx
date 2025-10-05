'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Brain, 
  Database, 
  Zap, 
  Target, 
  BarChart3,
  Upload,
  Settings,
  Eye
} from 'lucide-react';

const About: React.FC = () => {
  const features = [
    {
      icon: Brain,
      title: 'Advanced Artificial Intelligence',
      description: 'Cutting-edge machine learning architectures — from feature-based LightGBM baselines to physics-informed Transformers and CNNs — designed to detect exoplanets from raw light curves with unparalleled robustness and interpretability.',
      color: 'text-blue-400'
    },
    {
      icon: Database,
      title: 'Official NASA Data',
      description: 'Direct access to high-quality datasets from the Kepler, K2, and TESS missions via MAST, including over 17,000 validated light curves preprocessed by sector and ID for precise stellar signal recovery.',
      color: 'text-green-400'
    },
    {
      icon: Zap,
      title: 'Real‑Time Analysis',
      description: 'Instant evaluation of stellar objects using their light curves and IDs to determine exoplanet likelihood, complete with interactive reports, confidence intervals, and calibrated probability estimates.',
      color: 'text-yellow-400'
    },
    {
      icon: Target,
      title: 'Exceptional Accuracy',
      description: 'State-of-the-art algorithms inspired by NASA’s ExoMiner and enhanced with Transformer-based architectures built from scratch, achieving up to 92 % accuracy while minimizing false positives in exoplanet detection.',
      color: 'text-red-400'
    }
  ];

  const tools = [
    {
      icon: Upload,
      title: 'Data Analysis',
      description: 'Upload your CSV files and get instant predictions with confidence scores and detailed explanations.'
    },
    {
      icon: Settings,
      title: 'Custom Training',
      description: 'Retrain the models with your own labeled data to improve performance on your specific use cases.'
    },
    {
      icon: BarChart3,
      title: 'Advanced Statistics',
      description: 'View detailed performance metrics: accuracy, recall, F1‑score, and model performance over time.'
    },
    {
      icon: Eye,
      title: 'Three treatment methods',
      description: 'TSFRESH + Multi-View Transformer (Time-Series Model) -- ExoMiner (Deep Learning, State-of-the-Art) -- XGBoost Ensemble Model (Tabular Model)'
    }
  ];

  return (
    <section id="about" className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* En-tête de section */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            A Revolution in 
            <span className="gradient-text"> Exoplanet Detection</span>
          </h2>
          <p className="text-xl text-space-300 max-w-3xl mx-auto leading-relaxed">
            Exoplanet Hunter combines cutting‑edge artificial intelligence with the most precise astronomical
            data to automate the discovery of new worlds.
          </p>
        </motion.div>

        {/* Fonctionnalités principales */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-20">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              className="bg-space-800/30 backdrop-blur-sm border border-space-700 rounded-xl p-6 hover:border-primary-500/50 transition-all duration-300"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true }}
              whileHover={{ y: -5, scale: 1.02 }}
            >
              <feature.icon className={`h-12 w-12 ${feature.color} mb-4`} />
              <h3 className="text-lg font-semibold text-white mb-3">
                {feature.title}
              </h3>
              <p className="text-space-400 text-sm leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Méthode du Transit */}
        <motion.div
          className="rounded-2xl p-8 md:p-12 mb-20 border border-space-700/0"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-3xl font-bold text-white mb-6">
                The Transit Method
              </h3>
              <p className="text-space-300 mb-6 leading-relaxed">
                Our AI analyzes stellar light curves to detect brightness dips characteristic of a planet passing
                in front of its star. This method, used by the Kepler and TESS missions, makes it possible to
                identify exoplanets with remarkable precision.
              </p>
              <div className="space-y-3">
                {[
                  'Automatic transit detection',
                  'Orbital parameter analysis',
                  'Intelligent signal classification',
                  'Validation via machine learning'
                ].map((item, index) => (
                  <motion.div
                    key={index}
                    className="flex items-center space-x-3"
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    viewport={{ once: true }}
                  >
                    <div className="w-2 h-2 bg-primary-400 rounded-full"></div>
                    <span className="text-space-300">{item}</span>
                  </motion.div>
                ))}
              </div>
            </div>
            
            <div className="relative">
              <motion.div
                className="bg-space-800 rounded-xl p-6 border border-space-600"
                whileHover={{ scale: 1.05 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <div className="text-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 text-primary-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                <h4 className="text-xl font-semibold text-white mb-2">
                  Analyzed Variables
                </h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    {[
                    'Orbital period',
                    'Transit duration',
                    'Signal depth',
                    'Planetary radius',
                    'Stellar temperature',
                    'Stellar mass'
                    ].map((variable, index) => (
                      <div key={index} className="text-space-400 bg-space-700/50 rounded px-2 py-1">
                        {variable}
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </motion.div>

        {/* Outils disponibles */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h3 className="text-3xl font-bold text-white text-center mb-12">
            Integrated Professional Tools
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {tools.map((tool, index) => (
              <motion.div
                key={index}
                className="flex items-start space-x-4 p-6 bg-space-800/20 rounded-xl border border-space-700 hover:border-primary-500/50 transition-all duration-300"
                initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ scale: 1.02 }}
              >
                <div className="bg-primary-500/20 p-3 rounded-lg">
                  <tool.icon className="h-6 w-6 text-primary-400" />
                </div>
                <div>
                  <h4 className="text-lg font-semibold text-white mb-2">
                    {tool.title}
                  </h4>
                  <p className="text-space-400 text-sm leading-relaxed">
                    {tool.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Models: Detailed Overview */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="space-y-8 mt-16"
        >
          <h3 className="text-3xl font-bold text-white text-center">
            Models: Detailed Overview
          </h3>

          <div className="p-6 bg-space-800/20 rounded-xl border border-space-700">
            <h4 className="text-2xl font-semibold text-white mb-2">🪐 1. TSFRESH + Multi-View Transformer (Time-Series Model)</h4>
            <p className="text-space-300"><strong>Data Type</strong>: Light curves (raw flux over time)</p>
            <p className="text-space-300 mt-3">
              <strong>Description</strong>: This model processes the temporal brightness variations of stars recorded by TESS or Kepler. It combines TSFRESH (feature extraction) and a Multi-View Transformer (global/folded/local views) and fuses representations to detect true transits.
            </p>
            <p className="text-space-300 mt-3">
              <strong>Innovation</strong>: Hybrid interpretability + attention with uncertainty calibration.
            </p>
          </div>

          <div className="p-6 bg-space-800/20 rounded-xl border border-space-700">
            <h4 className="text-2xl font-semibold text-white mb-2">🚀 2. ExoMiner (Deep Learning, State-of-the-Art) - septober 2025 last version</h4>
            <p className="text-space-300"><strong>Data Type</strong>: Light curves (processed) + stellar metadata</p>
            <p className="text-space-300 mt-3">
              <strong>Description</strong>: NASA's CNN trained on Kepler, analyzing phase‑folded curves to separate true planets from false positives.
            </p>
            <p className="text-space-300 mt-3">
              <strong>Innovation</strong>: SoTA validation accuracy, explainability, operational usage on Kepler/TESS.
            </p>
          </div>

          <div className="p-6 bg-space-800/20 rounded-xl border border-space-700">
            <h4 className="text-2xl font-semibold text-white mb-2">💡 3. XGBoost Ensemble Model (Tabular Model)</h4>
            <p className="text-space-300"><strong>Data Type</strong>: Tabular KOI features (stellar + orbital)</p>
            <p className="text-space-300 mt-3">
              <strong>Description</strong>: Ensemble ML (XGBoost/Random Forest/Stacking) on precomputed features; fast, interpretable baseline.
            </p>
            <p className="text-space-300 mt-3">
              <strong>Innovation</strong>: &gt;83% accuracy with tuned hyperparameters; efficient and transparent.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border border-space-700/40 rounded-lg overflow-hidden">
              <thead>
                <tr className="bg-space-800/40">
                  <th className="py-3 px-4 text-space-300 font-semibold">Model</th>
                  <th className="py-3 px-4 text-space-300 font-semibold">Data Type</th>
                  <th className="py-3 px-4 text-space-300 font-semibold">Core Approach</th>
                  <th className="py-3 px-4 text-space-300 font-semibold">Innovation / Strength</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t border-space-700/40">
                  <td className="py-3 px-4 text-white">TSFRESH + Transformer</td>
                  <td className="py-3 px-4 text-space-300">Light curves (raw)</td>
                  <td className="py-3 px-4 text-space-300">Hybrid stats + deep sequential</td>
                  <td className="py-3 px-4 text-space-300">Multi‑view attention; feature extraction; uncertainty</td>
                </tr>
                <tr className="border-t border-space-700/40">
                  <td className="py-3 px-4 text-white">ExoMiner</td>
                  <td className="py-3 px-4 text-space-300">Light curves (folded)</td>
                  <td className="py-3 px-4 text-space-300">Deep CNN (NASA)</td>
                  <td className="py-3 px-4 text-space-300">SoTA accuracy; explainability</td>
                </tr>
                <tr className="border-t border-space-700/40">
                  <td className="py-3 px-4 text-white">XGBoost Ensemble</td>
                  <td className="py-3 px-4 text-space-300">Tabular KOI</td>
                  <td className="py-3 px-4 text-space-300">Gradient boosting</td>
                  <td className="py-3 px-4 text-space-300">Interpretable; efficient</td>
                </tr>
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default About;
