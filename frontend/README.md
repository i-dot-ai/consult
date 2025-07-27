# Frontend Proxy Server

This is a proxy server that enables gradual migration from the Django backend to a Node.js frontend.

## Architecture

The proxy server handles requests in this order:

1. **Frontend Static Assets** (`/frontend-static/*`) - Served directly from `./public/`
2. **Frontend Routes** - Routes migrated from backend, defined in `FRONTEND_ROUTES`
3. **Backend Proxy** - All other routes proxied to Django backend

## Migration Strategy

### Adding a New Frontend Route

1. Add the route path to the `FRONTEND_ROUTES` array in `server.js`:
   ```javascript
   const FRONTEND_ROUTES = [
     '/api/v2',           // New API endpoints
     '/new-dashboard',    // Migrated dashboard
     '/components/*'      // Component library
   ];
   ```

2. Implement the route handler by replacing the placeholder in the forEach loop:
   ```javascript
   FRONTEND_ROUTES.forEach(route => {
     if (route === '/api/v2') {
       app.use('/api/v2', require('./routes/api-v2'));
     } else if (route === '/new-dashboard') {
       app.use('/new-dashboard', require('./routes/dashboard'));
     }
     // ... other routes
   });
   ```

### Example Migration Process

1. **Phase 1**: Start with API endpoints
   - Migrate `/api/v2/*` endpoints to frontend
   - Keep existing `/api/*` routes in Django

2. **Phase 2**: Migrate UI components
   - Add new React/Vue components under `/components/*`
   - Gradually replace Django templates

3. **Phase 3**: Migrate full pages
   - Move complete pages like `/new-dashboard`
   - Update internal links to use new routes

### Environment Variables

- `BACKEND_URL` (required): Backend Django service URL
- `PORT` (optional): Frontend proxy port (default: 3000)

### Development

```bash
# Install dependencies
npm install

# Start development server
BACKEND_URL=http://localhost:8000 npm start

# Production
npm start
```

### Deployment

The server is configured for ECS Fargate deployment. Set the `BACKEND_URL` environment variable to your backend service URL.

### Logging

The server logs all requests showing whether they're handled by:
- Frontend (implemented routes)
- Backend (proxied routes)

This helps track migration progress and debug routing issues.