FROM python:3.11-alpine
RUN pip install --no-cache-dir flask requests gunicorn gevent
COPY orion_mock.py /app/orion_mock.py
WORKDIR /app
EXPOSE 1026
CMD ["gunicorn", "--worker-class", "gevent", "--workers", "4", "--bind", "0.0.0.0:1026", "--timeout", "30", "orion_mock:app"]
