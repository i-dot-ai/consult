# Use official Node.js runtime as base image
FROM node:20-alpine

# Set working directory in container
WORKDIR /app

# Copy package files
COPY package*.json ./

# Copy application code
COPY . .

# Remove existing node_modules and package-lock.json to fix rollup native module issue
RUN rm -rf node_modules package-lock.json

# Install dependencies fresh
RUN npm install

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs
RUN adduser -S astro -u 1001

# Change ownership of app directory
RUN chown -R astro:nodejs /app
USER astro

# Expose port (dev server port)
EXPOSE 4321

# Start the development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]