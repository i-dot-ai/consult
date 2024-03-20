# Use the Nginx image from Docker Hub
FROM nginx:alpine

# Copy your index.html file into the Nginx server
COPY index.html /usr/share/nginx/html/index.html

# Expose port 80 to the host so you can access your site
EXPOSE 80

# Start Nginx and keep it running in the foreground
CMD ["nginx", "-g", "daemon off;"]