FROM python:3.11-slim
WORKDIR /app

# Create a non-root user
RUN adduser --disabled-password --gecos "" myuser

# Switch to the non-root user
USER myuser

# Set up environment variables
ENV PATH="/home/myuser/.local/bin:$PATH"
ENV GOOGLE_GENAI_USE_VERTEXAI=1
ENV GOOGLE_CLOUD_PROJECT=my-lab-project-491212
ENV GOOGLE_CLOUD_LOCATION=us-central1

# Install dependencies
RUN pip install google-adk==1.28.0 fastapi uvicorn

# Copy agent
COPY --chown=myuser:myuser classifier_agent/ /app/classifier_agent/

# Copy main.py
COPY --chown=myuser:myuser main.py /app/main.py

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]