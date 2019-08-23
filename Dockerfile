FROM python:3.7
WORKDIR /app
COPY . /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN pip install python-telegram-bot
EXPOSE 80
ENV MODE prod
CMD ["python", "main.py"]