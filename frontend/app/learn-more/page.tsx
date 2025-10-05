"use client";

import * as React from "react";
import MegaMenu from "@/components/ui/mega-menu";
import type { MegaMenuItem } from "@/components/ui/mega-menu";
import Particles from "@/components/Particles";
import CardSwap, { Card } from "@/components/landing/CardSwap";
import TransitSection from "@/components/landing/TransitSection";
import About from "@/components/landing/About";
import styles from './page.module.css';
import TeamSection from "@/components/landing/TeamSection";
import FadeIn from "@/components/landing/FadeIn";

const LearnMorePage = () => {
  const NAV_ITEMS: MegaMenuItem[] = [
    { id: 1, label: "Learn more", link: "/learn-more" },
    { id: 2, label: "Home", link: "/home" },
    { id: 3, label: "Dashboard", link: "/dashboard" },
    { id: 4, label: "GitHub", link: "https://github.com/synaptiq-lab/exoplanet-hunter" }
  ];

  return (
    <div style={{ position: 'relative', width: '100%', minHeight: '100vh', background: 'black' }}>
      <div style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        <Particles
          className="particles-noninteractive"
          particleColors={["#ffffff", "#ffffff"]}
          particleCount={200}
          particleSpread={10}
          speed={0.1}
          particleBaseSize={100}
          moveParticlesOnHover={false}
          alphaParticles={false}
          disableRotation={false}
        />
      </div>

      <header className="relative z-30 flex w-full items-start justify-center p-6">
        <div className="relative">
          <MegaMenu items={NAV_ITEMS} />
        </div>
      </header>

      <main className="relative z-10">
        <div style={{ paddingTop: 48, paddingBottom: 64 }}>
          <FadeIn>
            <TeamSection />
          </FadeIn>
        </div>

        {/* Glow divider */}
        <div className={styles.divider} style={{ margin: '12px 0 28px 0' }} />

        <section style={{ position: 'relative', minHeight: 600, padding: '64px 24px' }}>
          <div style={{ maxWidth: 1100, margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, alignItems: 'center' }}>
            <FadeIn delayMs={0}>
              <div style={{ color: 'white' }}>
                <h2 style={{ fontSize: 35, lineHeight: 1.1, margin: 0 }}>
                  Space speaks
                  <br />
                  AI listens!
                </h2>
                <p style={{ opacity: 0.8, marginTop: 12, fontSize: 20, lineHeight: 1.1 }}>Artificial intelligence assisting Kepler, K2 and TESS to discover new worlds. Discover how AI is redefining the hunt for exoplanets.</p>
              </div>
            </FadeIn>

            <FadeIn delayMs={150}>
              <div style={{ height: 600, position: 'relative' }}>
                <CardSwap cardDistance={60} verticalDistance={70} delay={5000} pauseOnHover={false}>
                  <Card headerLabel="Kepler 1">
                    <img
                      src="/team/kepler_1.png"
                      alt="Kepler 1"
                      style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                      loading="lazy"
                    />
                  </Card>
                  <Card headerLabel="Kepler 2">
                    <img
                      src="/team/kepler_2.jpg"
                      alt="Kepler 2"
                      style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                      loading="lazy"
                    />
                  </Card>
                  <Card headerLabel="TESS">
                    <img
                      src="/team/tess.jpg"
                      alt="TESS"
                      style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                      loading="lazy"
                    />
                  </Card>
                </CardSwap>
              </div>
            </FadeIn>
          </div>
        </section>

        {/* Glow divider before transit section */}
        <div className={styles.dividerLarge} />

        <TransitSection />

        {/* Glow divider before About */}
        <div className={styles.dividerBeforeAbout} />

        {/* About section */}
        <div className={styles.pagePad}>
          <About />
        </div>
      </main>
    </div>
  );
};

export default LearnMorePage;


