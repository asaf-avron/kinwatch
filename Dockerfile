FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

ENV KINWATCH_HOST=0.0.0.0
ENV KINWATCH_PORT=8000
ENV KINWATCH_USE_FIXTURES=true
EXPOSE 8000

# AgentCore Runtime contract: bind 0.0.0.0:8000 and serve /mcp plus extra HTTP routes.
CMD ["uvicorn", "kinwatch.app:app", "--host", "0.0.0.0", "--port", "8000"]
