import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import './monaco/loader'; // ensure offline Monaco setup is registered
import { Providers } from './app/providers';
import App from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Providers>
      <App />
    </Providers>
  </StrictMode>
);
