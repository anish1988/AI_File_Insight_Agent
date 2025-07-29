# Use Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

# Expose Streamlit port
EXPOSE 8501

#RUN useradd user

#ENV HOME=/home/user \
  #  PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
#WORKDIR $HOME/app

# Copy the current directory contents into the container at $home/app Settings the owner to 
#COPY --chown=user . $HOME/app

# Run the Streamlit app
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
