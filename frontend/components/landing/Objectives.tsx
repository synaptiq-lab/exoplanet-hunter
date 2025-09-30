'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Rocket, 
  Users, 
  BookOpen, 
  Award, 
  Globe, 
  TrendingUp,
  Lightbulb,
  Heart
} from 'lucide-react';

const Objectives: React.FC = () => {
  const objectives = [
    {
      icon: Rocket,
      title: 'Accélérer la Découverte',
      description: 'Automatiser le processus de détection d\'exoplanètes pour analyser des milliers d\'observations en quelques secondes au lieu de mois de travail manuel.',
      color: 'from-blue-500 to-purple-600',
      stats: '1000x plus rapide'
    },
    {
      icon: Users,
      title: 'Démocratiser l\'Astronomie',
      description: 'Rendre les outils de recherche astronomique accessibles aux chercheurs, étudiants et passionnés du monde entier, sans expertise technique préalable.',
      color: 'from-green-500 to-teal-600',
      stats: 'Accessible à tous'
    },
    {
      icon: BookOpen,
      title: 'Éduquer et Inspirer',
      description: 'Créer une plateforme pédagogique interactive pour comprendre les méthodes de détection d\'exoplanètes et les missions spatiales.',
      color: 'from-yellow-500 to-orange-600',
      stats: 'Formation intégrée'
    },
    {
      icon: Award,
      title: 'Excellence Scientifique',
      description: 'Maintenir les plus hauts standards de précision et de fiabilité pour contribuer efficacement à la recherche astronomique mondiale.',
      color: 'from-red-500 to-pink-600',
      stats: '92% de précision'
    }
  ];

  const impact = [
    {
      icon: Globe,
      title: 'Impact Global',
      description: 'Contribuer à la découverte de nouvelles exoplanètes potentiellement habitables',
      value: '5000+'
    },
    {
      icon: TrendingUp,
      title: 'Recherche Accélérée',
      description: 'Réduction drastique du temps d\'analyse des données astronomiques',
      value: '95%'
    },
    {
      icon: Lightbulb,
      title: 'Innovation Continue',
      description: 'Amélioration constante des algorithmes grâce aux retours utilisateurs',
      value: '24/7'
    },
    {
      icon: Heart,
      title: 'Passion Partagée',
      description: 'Communauté grandissante de passionnés d\'astronomie et d\'IA',
      value: '∞'
    }
  ];

  return (
    <section className="py-20 bg-gradient-to-b from-space-900 to-space-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* En-tête */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Notre <span className="gradient-text">Mission</span>
          </h2>
          <p className="text-xl text-space-300 max-w-3xl mx-auto leading-relaxed">
            Révolutionner la découverte d'exoplanètes en combinant l'intelligence artificielle 
            avec la passion de l'exploration spatiale, pour un avenir où chacun peut contribuer 
            à l'expansion de nos connaissances de l'univers.
          </p>
        </motion.div>

        {/* Objectifs principaux */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-20">
          {objectives.map((objective, index) => (
            <motion.div
              key={index}
              className="relative group"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              viewport={{ once: true }}
            >
              <div className="relative bg-space-800/50 backdrop-blur-sm border border-space-700 rounded-2xl p-8 h-full hover:border-primary-500/50 transition-all duration-300 group-hover:scale-105">
                {/* Gradient de fond */}
                <div className={`absolute inset-0 bg-gradient-to-br ${objective.color} opacity-5 rounded-2xl group-hover:opacity-10 transition-opacity duration-300`}></div>
                
                {/* Contenu */}
                <div className="relative z-10">
                  <div className="flex items-center justify-between mb-6">
                    <div className={`p-4 rounded-xl bg-gradient-to-br ${objective.color} shadow-lg`}>
                      <objective.icon className="h-8 w-8 text-white" />
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-primary-400">
                        {objective.stats}
                      </div>
                    </div>
                  </div>
                  
                  <h3 className="text-2xl font-bold text-white mb-4">
                    {objective.title}
                  </h3>
                  
                  <p className="text-space-300 leading-relaxed">
                    {objective.description}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Section Impact */}
        <motion.div
          className="bg-gradient-to-r from-primary-900/20 to-purple-900/20 rounded-3xl p-8 md:p-12 border border-primary-500/20"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <div className="text-center mb-12">
            <h3 className="text-3xl md:text-4xl font-bold text-white mb-4">
              L'Impact d'Exoplanet Hunter
            </h3>
            <p className="text-xl text-space-300 max-w-2xl mx-auto">
              Ensemble, nous repoussons les frontières de la connaissance et 
              participons à l'une des plus grandes quêtes de l'humanité.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {impact.map((item, index) => (
              <motion.div
                key={index}
                className="text-center group"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ scale: 1.05 }}
              >
                <div className="bg-space-800/50 rounded-2xl p-6 border border-space-600 group-hover:border-primary-500/50 transition-all duration-300">
                  <item.icon className="h-12 w-12 text-primary-400 mx-auto mb-4" />
                  <div className="text-3xl font-bold text-white mb-2">
                    {item.value}
                  </div>
                  <h4 className="text-lg font-semibold text-white mb-3">
                    {item.title}
                  </h4>
                  <p className="text-space-400 text-sm leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Call to Action */}
        <motion.div
          className="text-center mt-16"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h3 className="text-2xl md:text-3xl font-bold text-white mb-6">
            Prêt à Explorer l'Univers ?
          </h3>
          <p className="text-lg text-space-300 mb-8 max-w-2xl mx-auto">
            Rejoignez la communauté des explorateurs d'exoplanètes et contribuez 
            à l'avancement de l'astronomie moderne.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <motion.button
              className="bg-primary-600 hover:bg-primary-700 text-white font-bold py-3 px-8 rounded-xl transition-all duration-300 transform hover:scale-105"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Commencer Maintenant
            </motion.button>
            
            <motion.button
              className="bg-transparent border-2 border-space-600 hover:border-primary-500 text-white font-medium py-3 px-8 rounded-xl transition-all duration-300"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Documentation
            </motion.button>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default Objectives;

