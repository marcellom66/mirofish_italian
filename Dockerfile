FROM python:3.11

# Install Node.js (>=18) and required tools / Installa Node.js (>=18) e strumenti necessari
RUN apt-get update \
  && apt-get install -y --no-install-recommends nodejs npm \
  && rm -rf /var/lib/apt/lists/*

# Copy uv from the official uv image / Copia uv dall'immagine ufficiale uv
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Copy dependency manifest files first to leverage cache / Copia prima i manifest delle dipendenze per sfruttare la cache
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY backend/pyproject.toml backend/uv.lock ./backend/

# Install dependencies (Node + Python) / Installa dipendenze (Node + Python)
RUN npm ci \
  && npm ci --prefix frontend \
  && cd backend && uv sync --frozen

# Copy project source code / Copia il codice sorgente del progetto
COPY . .

EXPOSE 3000 5001

# Start backend and frontend together (development mode) / Avvia backend e frontend insieme (modalita sviluppo)
CMD ["npm", "run", "dev"]