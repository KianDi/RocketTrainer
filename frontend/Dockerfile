FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start the development server (no build needed for dev)
CMD ["npm", "start"]
