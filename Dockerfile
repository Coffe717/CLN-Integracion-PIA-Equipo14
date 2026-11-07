# Usamos una imagen oficial y ligera de Python
FROM python:3.13-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos las dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos e instalamos las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código fuente del proyecto al contenedor
COPY . .

# Comando por defecto para ejecutar las pruebas con cobertura al iniciar el contenedor
CMD ["pytest", "tests/test_casos_pia.py", "--cov=src", "--cov-report=term-missing"]