"use client";

import React, { useEffect, useRef, useState } from 'react';

interface FadeInProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  delayMs?: number;
  distance?: number;
}

const FadeIn: React.FC<FadeInProps> = ({ children, className, style, delayMs = 0, distance = 16 }) => {
  const ref = useRef<HTMLDivElement | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          obs.disconnect();
        }
      },
      { threshold: 0.15 }
    );
    obs.observe(node);
    return () => obs.disconnect();
  }, []);

  const transitionStyle: React.CSSProperties = {
    opacity: isVisible ? 1 : 0,
    transform: isVisible ? 'translateY(0)' : `translateY(${distance}px)`,
    transition: 'opacity 600ms ease, transform 600ms ease',
    transitionDelay: isVisible ? `${delayMs}ms` : '0ms',
    ...style
  };

  return (
    <div ref={ref} className={className} style={transitionStyle}>
      {children}
    </div>
  );
};

export default FadeIn;


