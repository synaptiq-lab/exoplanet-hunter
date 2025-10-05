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
            What is the transit method?
          </h3>
        </FadeIn>
        <FadeIn delayMs={120}>
          <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
            <img
              src="/team/transit.gif"
              alt="Animation illustrating the transit method"
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
            When a planet passes in front of its star, the observed brightness drops slightly.
            By measuring these periodic dips in the light curve, we infer the presence of the exoplanet
            as well as clues about its size and orbit. Our mission was to build an application to detect
            exoplanets using machine learning models. We used data from the Kepler, K2, and TESS missions
            to train our models.
          </p>
        </FadeIn>
      </div>
    </section>
  );
};

export default TransitSection;


