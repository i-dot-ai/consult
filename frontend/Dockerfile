# Using Node 24.14.1 to match development environment (.nvmrc) and ci (.github/workflows/frontend-ci.yml)
FROM public.ecr.aws/docker/library/node:24.14.1-slim

# Set working directory in container
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install all dependencies including optional (needed for esbuild platform binaries)
RUN npm ci

# Copy application code
COPY frontend/ .

# Build the application (as root to avoid permission issues)
RUN npm run build

# Verify build output exists
RUN ls -la dist/
RUN ls -la dist/server/
RUN test -f dist/server/entry.mjs && echo "Server entry file exists" || echo "Server entry file NOT found"

# Create non-root user and group
RUN groupadd --system nonroot && useradd --system --gid nonroot --create-home nonroot

# Change ownership of app directory
RUN chown -R nonroot:nonroot /app

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

# Run under context of "nonroot" user
USER nonroot

# Start the application
CMD ["node", "/app/dist/server/entry.mjs"]