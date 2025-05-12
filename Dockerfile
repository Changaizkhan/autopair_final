FROM python:3.10.12-slim
 
WORKDIR /app
 
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install --upgrade openai
#RUN pip install --no-cache-dir -r requirements.txt
 
COPY . .
 
EXPOSE 5000
 
CMD ["python", "main.py"] 