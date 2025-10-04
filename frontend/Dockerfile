FROM node:18-alpine

WORKDIR /app

# Installation des dépendances
COPY package*.json ./
RUN npm install

# Copie du code source
COPY . .

EXPOSE 3000

# Utiliser le mode développement pour éviter les erreurs de build
CMD ["npm", "run", "dev"]
