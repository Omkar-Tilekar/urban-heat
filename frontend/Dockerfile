FROM node:20-alpine

WORKDIR /frontend

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 5173

# Start Vite with host flag so it listens on all interfaces inside Docker
CMD ["npm", "run", "dev", "--", "--host"]
