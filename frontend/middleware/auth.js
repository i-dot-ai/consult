const axios = require('axios');

class AuthMiddleware {
  constructor(backendUrl) {
    this.backendUrl = backendUrl;
  }

  /**
   * Middleware to validate user session with Django backend
   * Adds user information to req.user if authenticated
   */
  validateSession() {
    return async (req, res, next) => {
      try {
        // Skip auth validation for public routes
        const publicRoutes = ['/health', '/how-it-works/', '/privacy/', '/data-sharing/', '/get-involved/', '/'];
        const isPublicRoute = publicRoutes.some(route => 
          req.path === route || req.path.startsWith('/static/') || req.path.startsWith('/frontend-static/')
        );

        if (isPublicRoute) {
          return next();
        }

        // Forward cookies to backend for session validation
        const response = await axios.get(`${this.backendUrl}/api/user/me/`, {
          headers: {
            'Cookie': req.headers.cookie || '',
            'User-Agent': req.headers['user-agent'] || 'Frontend-Proxy/1.0'
          },
          timeout: 5000,
          validateStatus: (status) => status < 500 // Don't throw on 4xx errors
        });

        if (response.status === 200) {
          // User is authenticated, add user info to request
          req.user = response.data;
          req.isAuthenticated = true;
          console.log(`Authenticated user: ${req.user.email}`);
          return next();
        } else {
          // User not authenticated
          req.isAuthenticated = false;
          return this.handleUnauthenticated(req, res);
        }

      } catch (error) {
        console.error('Auth validation error:', error.message);
        
        // On backend connection error, pass through to backend
        // This maintains existing behavior if backend is temporarily unavailable
        req.isAuthenticated = false;
        return next();
      }
    };
  }

  /**
   * Middleware to require authentication for protected routes
   */
  requireAuth() {
    return (req, res, next) => {
      if (!req.isAuthenticated) {
        return this.handleUnauthenticated(req, res);
      }
      next();
    };
  }

  /**
   * Middleware to require dashboard access
   */
  requireDashboardAccess() {
    return (req, res, next) => {
      if (!req.isAuthenticated) {
        return this.handleUnauthenticated(req, res);
      }
      
      if (!req.user.has_dashboard_access) {
        return res.status(403).json({
          error: 'Dashboard access required',
          message: 'You do not have permission to access this resource'
        });
      }
      
      next();
    };
  }

  /**
   * Handle unauthenticated requests
   */
  handleUnauthenticated(req, res) {
    // For API requests, return JSON error
    if (req.path.startsWith('/api/')) {
      return res.status(401).json({
        error: 'Authentication required',
        message: 'Please log in to access this resource'
      });
    }
    
    // For web requests, redirect to login
    return res.redirect('/sign-in/');
  }

  /**
   * Get user info from request (utility method)
   */
  getUser(req) {
    return req.user || null;
  }

  /**
   * Check if user is authenticated (utility method)
   */
  isAuthenticated(req) {
    return req.isAuthenticated || false;
  }
}

module.exports = AuthMiddleware;