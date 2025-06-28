FROM python:3.9
WORKDIR /backend
COPY requirements.txt /backend
RUN pip3 install --upgrade pip -r requirements.txt
COPY main.py /backend
EXPOSE 8082

ENTRYPOINT python -u main.py
