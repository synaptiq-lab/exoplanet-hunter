"use client";

import React from 'react';
import FadeIn from './FadeIn';

interface TransitSectionProps {
  className?: string;
}

const TransitSection: React.FC<TransitSectionProps> = ({ className }) => {
  return (
    <section className={`transit-section ${className ?? ''}`.trim()} style={{ position: 'relative', padding: '0 24px 64px' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <FadeIn delayMs={0}>
          <h3 style={{ color: 'white', fontSize: 35, lineHeight: 1.1, margin: '0 0 16px 0', textAlign: 'center' }}>
            Qu'est-ce que la méthode du transit ?
          </h3>
        </FadeIn>
        <FadeIn delayMs={120}>
          <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
            <img
              src="/team/transit.gif"
              alt="Animation illustrant la méthode du transit"
              style={{
                width: '100%',
                maxWidth: 900,
                height: 'auto',
                display: 'block',
                borderRadius: 12,
                border: '1px solid rgba(255,255,255,0.12)',
                boxShadow: '0 10px 30px rgba(0,0,0,0.6), 0 0 40px rgba(120,80,255,0.2)'
              }}
              loading="lazy"
            />
          </div>
        </FadeIn>
        <FadeIn delayMs={240}>
          <p
            style={{
              color: 'rgba(255,255,255,0.9)',
              opacity: 0.85,
              marginTop: 12,
              fontSize: 16,
              lineHeight: 1.6,
              textAlign: 'center',
              maxWidth: 900,
              marginLeft: 'auto',
              marginRight: 'auto'
            }}
          >
            Lorsqu'une planète passe devant son étoile, la luminosité observée baisse légèrement.
            En mesurant ces creux périodiques dans la courbe de lumière, on déduit la présence de
            l'exoplanète ainsi que des indices sur sa taille et son orbite. Notre mission était de créer
            une application permettant de détecter les exoplanètes en utilisant des modèles de machine
            learning. Nous avons utilisé les données de la mission Kepler, K2 et TESS pour entraîner nos modèles.
          </p>
        </FadeIn>
      </div>
    </section>
  );
};

export default TransitSection;


