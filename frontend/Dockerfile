# Build stage
FROM node:20-alpine as build

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

# Pass API URL at build time
# In production with Nginx proxy, we use relative path /v1 or absolute URL if on different domain
# Here we default to /v1 so requests go to the same origin and Nginx proxies them
ARG VITE_API_BASE_URL=/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
