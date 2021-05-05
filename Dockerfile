FROM python:3.7
RUN mkdir /app
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
# Run run.py when the container launches
ENV ENV=staging
ENTRYPOINT ["python3"]
CMD ["app/api.py"]