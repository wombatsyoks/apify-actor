# Use the official Apify base image for Python
FROM apify/actor-python:3.11

# Copy actor code
COPY . ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the actor
CMD ["python", "main.py"]
