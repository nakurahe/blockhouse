FROM python:3.10-slim

WORKDIR /app

COPY main.py .
COPY requirements.txt .
COPY database.db .

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 80

CMD ["fastapi", "run", "main.py", "--port", "80"]