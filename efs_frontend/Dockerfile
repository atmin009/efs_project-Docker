FROM node:16 as build

WORKDIR /app

# คัดลอก dependencies
COPY package.json ./
COPY package-lock.json ./

# ติดตั้ง dependencies โดยใช้ --legacy-peer-deps
RUN npm install --legacy-peer-deps

# คัดลอกไฟล์โปรเจกต์
COPY . ./

# Build React
RUN npm run build

FROM httpd:2.4
COPY --from=build /app/build /usr/local/apache2/htdocs/
