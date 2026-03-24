#!/bin/bash

# Docker setup script for Resume Analyzer
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    print_status "Docker is installed and running"
}

# Check if Docker Compose is installed
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker Compose is installed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    mkdir -p nginx/ssl
    mkdir -p nginx/logs
    mkdir -p postgres
    mkdir -p redis
    mkdir -p secrets
    
    print_status "Directories created"
}

# Generate SSL certificates for development
generate_ssl_certs() {
    if [ ! -f "nginx/ssl/server.crt" ] || [ ! -f "nginx/ssl/server.key" ]; then
        print_status "Generating SSL certificates for development..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/server.key \
            -out nginx/ssl/server.crt \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        print_status "SSL certificates generated"
    else
        print_status "SSL certificates already exist"
    fi
}

# Create environment files
create_env_files() {
    if [ ! -f ".env" ]; then
        print_status "Creating .env file from example..."
        cp .env.example .env
        print_warning "Please update .env file with your actual configuration"
    else
        print_status ".env file already exists"
    fi
    
    if [ ! -f ".env.production" ]; then
        print_status "Creating .env.production file..."
        cat > .env.production << EOF
# Production Environment Variables
DEBUG=false
LOG_LEVEL=WARNING
API_WORKERS=4

# Database
POSTGRES_PASSWORD=\${POSTGRES_PASSWORD:-$(openssl rand -base64 32)}

# Security
SECRET_KEY=\${SECRET_KEY:-$(openssl rand -base64 64)}

# AWS (set these with your actual values)
AWS_ACCESS_KEY_ID=your-production-access-key
AWS_SECRET_ACCESS_KEY=your-production-secret-key
AWS_S3_BUCKET=your-production-s3-bucket
AWS_DYNAMODB_TABLE=your-production-dynamodb-table
AWS_SQS_QUEUE_URL=your-production-sqs-queue-url

# DeepSeek API
DEEPSEEK_API_KEY=your-production-deepseek-api-key
EOF
        print_warning "Please update .env.production with your actual production values"
    else
        print_status ".env.production file already exists"
    fi
}

# Create secrets for production
create_secrets() {
    if [ ! -f "secrets/grafana_admin_password.txt" ]; then
        print_status "Creating Grafana admin password..."
        openssl rand -base64 32 > secrets/grafana_admin_password.txt
        print_status "Grafana admin password created in secrets/grafana_admin_password.txt"
    fi
    
    if [ ! -f "secrets/grafana_secret_key.txt" ]; then
        print_status "Creating Grafana secret key..."
        openssl rand -base64 64 > secrets/grafana_secret_key.txt
        print_status "Grafana secret key created"
    fi
}

# Create monitoring configuration
create_monitoring_config() {
    # Prometheus configuration
    cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'resume-analyzer'
    static_configs:
      - targets: ['resume-analyzer:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

    # Grafana datasource
    cat > monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    print_status "Monitoring configuration created"
}

# Create Nginx configuration
create_nginx_config() {
    cat > nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream app {
        server resume-analyzer:8000;
    }

    server {
        listen 80;
        server_name localhost;
        return 301 https://\$server_name\$request_uri;
    }

    server {
        listen 443 ssl;
        server_name localhost;

        ssl_certificate /etc/nginx/ssl/server.crt;
        ssl_certificate_key /etc/nginx/ssl/server.key;

        location / {
            proxy_pass http://app;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /ws {
            proxy_pass http://app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF

    print_status "Nginx configuration created"
}

# Build and start services
start_development() {
    print_status "Building and starting development environment..."
    
    docker-compose down --remove-orphans
    docker-compose build
    docker-compose up -d
    
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    if docker-compose ps | grep -q "Up (healthy)"; then
        print_status "Services are running and healthy!"
        print_status "Application available at: https://localhost"
        print_status "API docs available at: https://localhost/docs"
        print_status "Grafana available at: http://localhost:3000 (admin/admin)"
        print_status "Flower (Celery) available at: http://localhost:5555"
    else
        print_warning "Some services may not be healthy. Check with 'docker-compose ps'"
    fi
}

# Start production environment
start_production() {
    print_status "Building and starting production environment..."
    
    docker-compose -f docker-compose.prod.yml down --remove-orphans
    docker-compose -f docker-compose.prod.yml build
    docker-compose -f docker-compose.prod.yml up -d
    
    print_status "Production environment started"
}

# Main execution
main() {
    print_status "Resume Analyzer Docker Setup"
    print_status "============================"
    
    check_docker
    check_docker_compose
    create_directories
    generate_ssl_certs
    create_env_files
    create_secrets
    create_monitoring_config
    create_nginx_config
    
    case "${1:-dev}" in
        "dev"|"development")
            start_development
            ;;
        "prod"|"production")
            start_production
            ;;
        "setup-only")
            print_status "Setup completed. Run './scripts/docker-setup.sh dev' to start development environment."
            ;;
        *)
            print_error "Usage: $0 [dev|prod|setup-only]"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"