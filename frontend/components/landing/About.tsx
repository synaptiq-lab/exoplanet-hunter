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
      title: 'Intelligence Artificielle Avancée',
      description: 'Modèles de machine learning optimisés spécifiquement pour la détection d\'exoplanètes utilisant les dernières techniques d\'apprentissage automatique.',
      color: 'text-blue-400'
    },
    {
      icon: Database,
      title: 'Données NASA Officielles',
      description: 'Accès direct aux datasets des missions Kepler, K2 et TESS avec plus de 17,000 observations astronomiques validées.',
      color: 'text-green-400'
    },
    {
      icon: Zap,
      title: 'Analyse en Temps Réel',
      description: 'Traitement ultra-rapide de milliers d\'observations avec des résultats instantanés et des visualisations interactives.',
      color: 'text-yellow-400'
    },
    {
      icon: Target,
      title: 'Précision Exceptionnelle',
      description: 'Algorithmes optimisés pour minimiser les faux positifs avec une précision de 92% dans la classification des exoplanètes.',
      color: 'text-red-400'
    }
  ];

  const tools = [
    {
      icon: Upload,
      title: 'Analyse de Données',
      description: 'Téléversez vos fichiers CSV et obtenez des prédictions instantanées avec scores de confiance et explications détaillées.'
    },
    {
      icon: Settings,
      title: 'Entraînement Personnalisé',
      description: 'Réentraînez les modèles avec vos propres données étiquetées pour améliorer les performances sur vos cas d\'usage spécifiques.'
    },
    {
      icon: BarChart3,
      title: 'Statistiques Avancées',
      description: 'Consultez les métriques de performance détaillées : précision, recall, F1-score et évolution temporelle des modèles.'
    },
    {
      icon: Eye,
      title: 'Exploration Interactive',
      description: 'Explorez vos datasets téléversés avec des outils de visualisation avancés et des filtres intelligents.'
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
            Une Révolution dans la 
            <span className="gradient-text"> Détection d'Exoplanètes</span>
          </h2>
          <p className="text-xl text-space-300 max-w-3xl mx-auto leading-relaxed">
            Exoplanet Hunter combine l'intelligence artificielle de pointe avec les données 
            astronomiques les plus précises pour automatiser la découverte de nouveaux mondes.
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
                La Méthode du Transit
              </h3>
              <p className="text-space-300 mb-6 leading-relaxed">
                Notre IA analyse les courbes de lumière stellaire pour détecter les baisses 
                de luminosité caractéristiques du passage d'une planète devant son étoile. 
                Cette méthode, utilisée par les missions Kepler et TESS, permet d'identifier 
                des exoplanètes avec une précision remarquable.
              </p>
              <div className="space-y-3">
                {[
                  'Détection automatique des transits',
                  'Analyse des paramètres orbitaux',
                  'Classification intelligente des signaux',
                  'Validation par apprentissage automatique'
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
                    Variables Analysées
                  </h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    {[
                      'Période orbitale',
                      'Durée du transit',
                      'Profondeur du signal',
                      'Rayon planétaire',
                      'Température stellaire',
                      'Masse stellaire'
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
            Outils Professionnels Intégrés
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
      </div>
    </section>
  );
};

export default About;
