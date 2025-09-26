# Build Stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files and install node modules
COPY package*.json ./
RUN npm install

# Copy all source code
COPY . .

# Build production files
RUN npm run build

# Production Stage
FROM nginx:stable-alpine

# Copy built files to nginx html folder
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
