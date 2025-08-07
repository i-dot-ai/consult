import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const BACKEND_URL = process.env.BACKEND_URL;

// Validate required environment variable
if (!BACKEND_URL) {
  console.error('ERROR: BACKEND_URL environment variable is required');
  console.error('Please set BACKEND_URL to the backend service URL (e.g., http://backend:8000)');
  process.exit(1);
}

// Routes handled by frontend (add routes here as you migrate them)
const FRONTEND_ROUTES = [
  '/health'
];

// Static file serving for frontend assets
app.use('/frontend-static', express.static(path.join(__dirname, 'public')));

// Frontend health check endpoint
app.get('/health', (req, res) => {
  console.log(`Handling ${req.method} ${req.url} in frontend`);
  res.json({
    status: 'healthy',
    service: 'frontend-proxy',
    timestamp: new Date().toISOString(),
    backend_target: BACKEND_URL,
    frontend_routes: FRONTEND_ROUTES
  });
});

// Create proxy middleware for backend routes
const backendProxy = createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  ws: true,
  logLevel: 'info',
  onError: (err, req, res) => {
    console.error('Backend proxy error:', err.message);
    res.status(500).send('Backend proxy error');
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`Proxying ${req.method} ${req.url} to backend: ${BACKEND_URL}${req.url}`);
  }
});

// Proxy all remaining requests to Django backend
app.use('/', backendProxy);

app.listen(PORT, () => {
  console.log(`Frontend proxy server running on port ${PORT}`);
  console.log(`Proxying requests to backend: ${BACKEND_URL}`);
  console.log(`Frontend routes: ${FRONTEND_ROUTES.length > 0 ? FRONTEND_ROUTES.join(', ') : 'none yet'}`);
});
