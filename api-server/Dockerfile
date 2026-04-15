FROM python:3.14-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files first for better layer caching
COPY pyproject.toml .python-version ./

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
