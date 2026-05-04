FROM alpine:3.20

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    redis \
    bash \
    git

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

RUN ls -l /app

RUN git clone https://github.com/asmirnov69/JupiterLI
RUN python3 -m venv venv
RUN /app/venv/bin/pip install /app/JupiterLI/

# Install Python dependencies
#RUN pip3 install --no-cache-dir -r requirements.txt
#RUN pip3 install git+https://github.com/asmirnov69/JupiterLI

# Make startup script executable
RUN chmod +x /app/start.sh

# Expose Redis port (optional)
EXPOSE 6379

# Start everything
CMD ["/app/start.sh"]
