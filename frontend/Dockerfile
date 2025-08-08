# Use official Node.js runtime as base image
FROM node:20-slim

# Set working directory in container
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY frontend/ .

# Create non-root user for security
RUN groupadd -g 1001 nodejs
RUN useradd -r -u 1001 -g nodejs -m nextjs

# Change ownership of app directory
RUN chown -R nextjs:nodejs /app
RUN chown -R nextjs:nodejs /home/nextjs

# Switch to non-root user
USER nextjs

# Build the application
RUN npm run build

# Verify build output exists
RUN ls -la dist/
RUN ls -la dist/server/
RUN test -f dist/server/entry.mjs && echo "Server entry file exists" || echo "Server entry file NOT found"

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

# Start the application
CMD ["node", "/app/dist/server/entry.mjs"]