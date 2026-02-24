# Using Node 20.18.0 to match development environment (.nvmrc) and ci (.github/workflows/frontend-ci.yml)
FROM public.ecr.aws/docker/library/node:20.18.0-slim

# Set working directory in container
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install all dependencies including optional (needed for esbuild platform binaries)
RUN npm ci

# Copy application code
COPY frontend/ .

# Create non-root user and group
RUN groupadd --system nonroot && useradd --system --gid nonroot nonroot

# Change ownership of app directory
RUN chown -R nonroot:nonroot /app

# Run under context of "nonroot" user
USER nonroot

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