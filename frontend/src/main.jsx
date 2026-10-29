import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import { AuthProvider } from './core/auth/AuthContext.jsx';
import { ToastProvider } from './core/ui/index.js';
import { initTheme } from './core/utils/theme.js';
import './styles/tokens.css';
import './styles/base.css';
import './styles/components.css';

initTheme();

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  </StrictMode>,
);
