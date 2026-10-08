## STAGE 1: Builder
FROM python:3.12-slim AS builder

# Set up tool configuration variables
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 

WORKDIR /build

COPY requirements-runtime.lock .

#Install only runtime dependencies into a dedicated target folder
RUN pip install --upgrade pip && \
    pip install --target=/build/runtime-packages -r requirements-runtime.lock


## STAGE 2: Runtime
FROM python:3.12-slim AS runtime

#Environment settings appropriate for Flask and Gunicorn
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production 

#Create a secure, non-root system user and group (UID/GID 10001)    
RUN groupadd -g 10001 appgroup && \
useradd -u 10001 -g appgroup -m -s /sbin/nologin appuser

WORKDIR /app

# Copy the pre-installed runtime dependencies from the builder stage
COPY --from=builder /build/runtime-packages /app/runtime-packages

# Copy the rest of the application source code into the container
COPY . .

#Ensure the non-root user owns the application working directory entirely
RUN chown -R appuser:appgroup /app

# Switch context to the non-root application user for execution
USER appuser

#Extend Python path so the app can locate the isolated runtime packages
ENV PYTHONPATH=/app/runtime-packages

#Expose the port that the Flask application will run on
EXPOSE 8000

#gunicorn command to binding all interfaces on port 8000 and loading via wsgi
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app"]
