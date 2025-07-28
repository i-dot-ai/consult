# Frontend Authentication Integration

This frontend proxy server now includes authentication integration with the Django backend.

## How It Works

1. **Session Validation**: The frontend validates user sessions by calling the Django backend's `/api/user/me/` endpoint
2. **Middleware Integration**: Auth middleware runs on every request to validate sessions and add user info to `req.user`
3. **Route Protection**: Different levels of protection available:
   - Public routes (no auth required)
   - Authenticated routes (requires login)
   - Dashboard routes (requires dashboard access permission)

## New Features Added

### Backend Changes
- **User API Endpoint**: `GET /api/user/me/` returns current user info
- **User Serializer**: Exposes user email, staff status, and dashboard access

### Frontend Changes
- **Auth Middleware**: Validates sessions with backend and manages user state
- **Protected Routes**: Sample routes demonstrating auth integration
- **Error Handling**: Proper 401/403 responses and redirects

## Available Routes

### Public Routes (No Auth Required)
- `/health` - Health check
- `/how-it-works/`, `/privacy/`, etc. - Info pages
- `/` - Home page

### Authenticated Routes
- `/api/frontend/user` - Sample API endpoint requiring auth
- `/consultations/` - Consultation list (proxied to backend)


## Testing the Integration

### 1. Start the Services
```bash
# Start Django backend
cd /Users/george.burton/consult
python manage.py runserver 8000

# Install frontend dependencies and start
cd frontend
npm install
BACKEND_URL=http://localhost:8000 npm start
```

### 2. Test Authentication Flow

1. **Visit protected route while logged out**:
   - Go to `http://localhost:3000/api/frontend/user`
   - Should return 401 Unauthorized

2. **Log in via Django magic link**:
   - Use the Django sign-in form at `http://localhost:3000/sign-in/`
   - Enter your email and click magic link

3. **Test protected routes while logged in**:
   - Visit `http://localhost:3000/api/frontend/user` - should return user JSON

4. **Test API authentication**:
   ```bash
   # Without session cookie (should fail)
   curl http://localhost:3000/api/frontend/user
   
   # With valid session cookie (should succeed)
   curl -H "Cookie: sessionid=your-session-id" http://localhost:3000/api/frontend/user
   ```

## Environment Variables

- `BACKEND_URL`: Django backend URL (e.g., `http://localhost:8000` or internal ECS service URL)
- `PORT`: Frontend server port (default: 3000)

## Migration Strategy

To migrate existing Django routes to the frontend:

1. Add route path to `FRONTEND_ROUTES` array
2. Create route handler with appropriate auth middleware:
   ```javascript
   app.get('/new-route', authMiddleware.requireAuth(), (req, res) => {
     // Handle route in frontend
   });
   ```
3. Remove route from Django URLs (or keep as fallback)

## Auth Middleware Methods

```javascript
// Apply to all routes for session validation
app.use(authMiddleware.validateSession());

// Require authentication
app.get('/protected', authMiddleware.requireAuth(), handler);

// Require dashboard access
app.get('/dashboard', authMiddleware.requireDashboardAccess(), handler);

// Utility methods
const user = authMiddleware.getUser(req);
const isAuth = authMiddleware.isAuthenticated(req);
```

## Error Handling

- **401 Unauthorized**: Returns JSON for API routes, redirects for web routes
- **403 Forbidden**: Returns JSON error for dashboard access violations
- **Backend Connection Errors**: Gracefully falls back to proxying to backend

## Security Notes

- Sessions are validated on every request to ensure up-to-date permissions
- No user data is cached in frontend - always fetched from backend
- CSRF protection is maintained through Django backend
- All authentication logic remains in Django - frontend only validates sessions