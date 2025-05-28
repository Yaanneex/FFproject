# Utilisez une image Python officielle avec Debian (compatible GeoPandas)
FROM python:3.11-slim-bookworm  # Python 3.11 + Debian 12 (stable pour GDAL)

# Installez les dépendances système critiques (pour GeoPandas, Folium, etc.)
RUN apt-get update && apt-get install -y \
    libspatialindex-dev \
    gdal-bin \
    libgdal-dev \
    python3-gdal \  # Nécessaire pour GeoPandas
    && rm -rf /var/lib/apt/lists/*

# Définissez le répertoire de travail
WORKDIR /app

# Copiez les fichiers nécessaires
COPY requirements.txt .
COPY app.py .

# Installez les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Configurez Streamlit
RUN mkdir -p /root/.streamlit
RUN echo "[server]\n\
headless = true\n\
port = 8501\n\
enableCORS = false\n\
" > /root/.streamlit/config.toml

# Exposez le port et lancez l'application
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
