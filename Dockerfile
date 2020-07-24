FROM microsoft/azure-cli:latest

ADD requirements.txt .
RUN pip install -r requirements.txt
ADD . .

CMD [ "/usr/local/bin/python3", "-u", "app.py" ]

