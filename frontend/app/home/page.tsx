"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import Galaxy from '@/components/Galaxy';
import styles from './page.module.css';

const LandingPage = () => {
  const [hue, setHue] = useState(140);

  return (
    <div className={styles.container}>
      <Galaxy 
        mouseInteraction={true}
        mouseRepulsion={true}
        density={1}
        glowIntensity={0.3}
        saturation={0}
        hueShift={hue}
      />

      {/* Top nav pill */}
      <div className={styles.nav}>
        <div className={styles.brand}>
          <span style={{ fontSize: 24 }}>✳️</span>
          <span>EXOPLANET HUNTER</span>
        </div>
        <nav className={styles.navLinks}>
          <Link href="/home" style={{ color: '#EDEDED', textDecoration: 'none' }}>Home</Link>
          <Link href="#" style={{ color: '#EDEDED', textDecoration: 'none' }}>Docs</Link>
        </nav>
      </div>

      {/* Center hero */}
      <div className={styles.hero}>
        {/* New Background pill */}
        <button
          onClick={() => setHue((h) => (h + 40) % 360)}
          className={styles.newBtn}
        >
          <span style={{ fontSize: 18 }}>▚▚</span>
          To new heights !
        </button>

        {/* Title */}
        <h1 style={{ fontSize: 64, lineHeight: 1.05, margin: 0, letterSpacing: -1.2 }}>
          They couldn't find them,
          <br />
          until we did it.
        </h1>

        {/* CTA buttons */}
        <div className={styles.ctaRow}>
          <Link
            href="/learn-more"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '14px 24px',
              borderRadius: 48,
              background: 'white',
              color: '#111',
              fontWeight: 700,
              textDecoration: 'none',
              minWidth: 160
            }}
          >
            Get Started
          </Link>
          <Link
            href="/learn-more"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '14px 24px',
              borderRadius: 48,
              background: 'rgba(24,24,28,0.7)',
              color: '#cfcfcf',
              border: '1px solid rgba(255,255,255,0.2)',
              textDecoration: 'none',
              minWidth: 160,
              fontWeight: 700
            }}
          >
            Learn More
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;


