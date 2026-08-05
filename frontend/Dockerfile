# Etapa 1: build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Etapa 2: servir estáticos con nginx (imagen final ligera)
FROM nginx:alpine
# Config custom con headers de seguridad (issue #41) y SPA routing.
# Reemplaza el default.conf que trae la imagen base.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
