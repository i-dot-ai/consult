# Use official Node.js runtime as base image
FROM --platform=linux/amd64 node:20-slim

# Install build tools for native dependencies
RUN apt-get update && apt-get install -y python3 make g++ && rm -rf /var/lib/apt/lists/*

# Set working directory in container
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install
# Rebuild native dependencies for container architecture
RUN npm rebuild

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

# Force reinstall problematic native dependencies
RUN npm uninstall lightningcss @tailwindcss/vite tailwindcss && npm install lightningcss @tailwindcss/vite tailwindcss

# Build the application
RUN npm run build

# Expose port
EXPOSE 4321

# Start the application
CMD ["npm", "start"]