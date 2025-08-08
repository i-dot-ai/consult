# Use official Node.js runtime as base image
FROM node:20-slim

# Set working directory in container
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY frontend/ .

# Build the application
RUN npm run build

# Create non-root user for security
RUN groupadd -g 1001 nodejs
RUN useradd -r -u 1001 -g nodejs -m nextjs

# Change ownership of app directory
RUN chown -R nextjs:nodejs /app
RUN chown -R nextjs:nodejs /home/nextjs
USER nextjs

# Expose port
EXPOSE 4321

# Start the application
CMD ["npm", "start"]