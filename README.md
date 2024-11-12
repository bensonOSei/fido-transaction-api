# Project Installation Guide

This guide covers both standard Python installation and Docker-based installation methods.

## Standard Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <project-directory>
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate Secret Key

```bash
# Ensure the script is executable
chmod +x scripts/generate_key.py

# Generate the secret key
./scripts/generate_key.py
```

### 5. Start the Application

```bash
uvicorn main:app --reload
```

## Docker Installation

### Build and Start with Docker Compose

```bash
docker-compose up --build
```

This will:

- Build the Docker image
- Start all required services
- Set up the application environment

### 3. Generate Secret Key (First Time Only)

```bash
# Execute the key generation script inside the container
docker-compose exec web ./scripts/generate_key.py
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
DATABASE_URL=postgresql://user:password@db:5432/dbname
SECRET_KEY=<generated-secret-key>
# Add other environment variables as needed
```

### Common Issues

1. **Permission Denied for generate_key.py**

   ```bash
   chmod +x scripts/generate_key.py
   ```

2. **Docker Container Won't Start**
   - Check if ports are already in use
   - Ensure Docker daemon is running
   - Verify Docker Compose file syntax

3. **Database Connection Issues**
   - Ensure PostgreSQL service is running
   - Check database credentials in .env file

## API Documentation

Once the application is running:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
