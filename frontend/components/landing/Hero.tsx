'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Rocket, ArrowRight, Sparkles, Globe, Brain } from 'lucide-react';
import Link from 'next/link';

const Hero: React.FC = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Fond animé avec étoiles */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 opacity-20">
          {[...Array(50)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-white rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                opacity: [0.3, 1, 0.3],
                scale: [1, 1.5, 1],
              }}
              transition={{
                duration: 2 + Math.random() * 3,
                repeat: Infinity,
                delay: Math.random() * 2,
              }}
            />
          ))}
        </div>
        
        {/* Planètes flottantes */}
        <motion.div
          className="absolute top-20 left-10 w-8 h-8 bg-primary-500 rounded-full opacity-60"
          animate={{
            y: [0, -30, 0],
            x: [0, 15, 0],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute top-1/3 right-20 w-12 h-12 bg-yellow-400 rounded-full opacity-40"
          animate={{
            y: [0, 40, 0],
            x: [0, -20, 0],
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute bottom-1/3 left-1/4 w-6 h-6 bg-purple-400 rounded-full opacity-50"
          animate={{
            y: [0, -35, 0],
            x: [0, 25, 0],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          {/* Icône principale */}
          <motion.div
            className="flex justify-center mb-8"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          >
            <div className="relative">
              <Globe className="h-24 w-24 text-primary-400 animate-spin-slow" />
              <motion.div
                className="absolute -top-3 -right-3 h-8 w-8 bg-yellow-400 rounded-full flex items-center justify-center"
                animate={{ 
                  scale: [1, 1.2, 1],
                  rotate: [0, 180, 360]
                }}
                transition={{ 
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              >
                <Sparkles className="h-4 w-4 text-yellow-900" />
              </motion.div>
            </div>
          </motion.div>

          {/* Titre principal */}
          <h1 className="text-6xl md:text-8xl font-bold mb-6">
            <span className="gradient-text">Exoplanet</span>
            <br />
            <span className="text-white">Hunter</span>
          </h1>
          
          {/* Sous-titre */}
          <p className="text-xl md:text-2xl text-space-300 mb-8 max-w-4xl mx-auto leading-relaxed">
            Découvrez des mondes lointains grâce à l'intelligence artificielle et aux données 
            des missions spatiales <span className="text-primary-400 font-semibold">NASA</span>
          </p>

          {/* Badges des missions */}
          <div className="flex flex-wrap justify-center items-center gap-4 mb-12">
            {[
              { name: 'Kepler', icon: Rocket, color: 'bg-blue-500/20 text-blue-400 border-blue-500/50' },
              { name: 'K2', icon: Brain, color: 'bg-purple-500/20 text-purple-400 border-purple-500/50' },
              { name: 'TESS', icon: Sparkles, color: 'bg-green-500/20 text-green-400 border-green-500/50' }
            ].map((mission, index) => (
              <motion.div
                key={mission.name}
                className={`flex items-center space-x-2 px-4 py-2 rounded-full border ${mission.color}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                whileHover={{ scale: 1.05 }}
              >
                <mission.icon className="h-5 w-5" />
                <span className="font-medium">Mission {mission.name}</span>
              </motion.div>
            ))}
          </div>

          {/* Boutons d'action */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <Link href="/dashboard">
              <motion.button
                className="group bg-primary-600 hover:bg-primary-700 text-white font-bold py-4 px-8 rounded-xl text-lg transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-primary-500/50 shadow-2xl shadow-primary-500/25"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
              >
                <span className="flex items-center space-x-3">
                  <span>Commencer l'Exploration</span>
                  <ArrowRight className="h-6 w-6 group-hover:translate-x-1 transition-transform" />
                </span>
              </motion.button>
            </Link>

            <motion.button
              className="group bg-transparent border-2 border-space-600 hover:border-primary-500 text-white font-medium py-4 px-8 rounded-xl text-lg transition-all duration-300"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              onClick={() => document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' })}
            >
              <span className="flex items-center space-x-3">
                <span>En Savoir Plus</span>
                <motion.div
                  animate={{ y: [0, 5, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  ↓
                </motion.div>
              </span>
            </motion.button>
          </div>

          {/* Statistiques */}
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16 max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
          >
            {[
              { number: '5000+', label: 'Exoplanètes Confirmées', icon: Globe },
              { number: '17000+', label: 'Observations Analysées', icon: Brain },
              { number: '92%', label: 'Précision IA', icon: Sparkles }
            ].map((stat, index) => (
              <motion.div
                key={index}
                className="text-center p-6 rounded-xl bg-space-800/30 backdrop-blur-sm border border-space-700"
                whileHover={{ scale: 1.05, y: -5 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <stat.icon className="h-8 w-8 text-primary-400 mx-auto mb-3" />
                <div className="text-3xl font-bold text-white mb-2">{stat.number}</div>
                <div className="text-space-400 text-sm">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};

export default Hero;

