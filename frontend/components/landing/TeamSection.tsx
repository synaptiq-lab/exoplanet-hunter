"use client";

import React from 'react';
import ProfileCard from './ProfileCard';

const TeamSection: React.FC = () => {
  const team = [
    {
      name: 'Anto BENEDETTI',
      title: 'Software Engineer',
      handle: 'anto',
      avatarUrl: '/team/anto.png'
    },
    {
      name: 'Divin BADIABO',
      title: 'ML Engineer',
      handle: 'divin',
      avatarUrl: '/team/divin.png'
    },
    {
      name: 'Hugo HOUNTONDJI',
      title: 'Project Lead',
      handle: 'hugo',
      avatarUrl: '/team/hugo.png'
    },
    {
      name: 'Evan GREVEN',
      title: 'Data Scientist',
      handle: 'evan',
      avatarUrl: '/team/evan.png'
    },
    {
      name: 'Lucas BONERE',
      title: 'Frontend Engineer',
      handle: 'lucas',
      avatarUrl: '/team/lucas.png'
    }
  ];

  return (
    <section style={{ position: 'relative', zIndex: 10, padding: '48px 24px' }}>
      <h2 style={{ color: 'white', textAlign: 'center', marginBottom: 24, letterSpacing: 6, fontSize: 35 }}>OUR TEAM</h2>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(5, minmax(0, 1fr))',
          gap: 16,
          alignItems: 'stretch'
        }}
      >
        {team.map((m, idx) => (
          <div key={m.handle}>
            <ProfileCard
              name={m.name}
              title=""
              handle={m.handle}
              status="Online"
              contactText="Contact Me"
              avatarUrl={m.avatarUrl}
              avatarScale={m.handle === 'lucas' ? 1.50 : m.handle === 'anto' ? 0.88 : 1}
              avatarBottomOffset={m.handle === 'lucas' ? 0 : m.handle === 'anto' ? 0 : 2}
              showUserInfo={true}
              enableTilt={true}
              enableMobileTilt={false}
              onContactClick={() => console.log('Contact clicked', m.handle)}
            />
          </div>
        ))}
      </div>
    </section>
  );
};

export default TeamSection;


