# AI Video Analyzer - Docker Deployment
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user for better security and macOS compatibility
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /app && \
    chown -R app:app /app

# Set working directory
WORKDIR /app

# Switch to app user
USER app

# Copy requirements first for better caching
COPY --chown=app:app requirements.txt .

# Install PyTorch CPU first (for better caching)
RUN pip install --no-cache-dir --user torch>=2.0.0 --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy the application code
COPY --chown=app:app . .

# Create directories for results and other data (with proper permissions)
RUN mkdir -p results rubrics overrides

# Add local bin to PATH for user-installed packages
ENV PATH="/home/app/.local/bin:$PATH"
ENV PYTHONPATH=/app

# Expose Streamlit port
EXPOSE 8501

# Set environment variables
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run the application
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]