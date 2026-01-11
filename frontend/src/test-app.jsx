// Temporary minimal React app to verify the setup
import React from 'react';
import { createRoot } from 'react-dom/client';

function App() {
  return (
    <div style={{ padding: '20px', fontFamily: 'system-ui' }}>
      <h1 style={{ color: '#2563eb' }}>Finance App</h1>
      <p>Frontend is loading successfully! ✓</p>
      <p>The full React app will load here.</p>
    </div>
  );
}

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(<App />);
}

