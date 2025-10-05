import React from 'react';
import Layout from '@/components/Layout';
import Hero from '@/components/landing/Hero';
import About from '@/components/landing/About';
import Objectives from '@/components/landing/Objectives';

const HomePage = () => {
  return (
    <Layout>
      <Hero />
      <About />
      <Objectives />
    </Layout>
  );
};

export default HomePage;


