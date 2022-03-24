FROM python:3.8

COPY  ./requirements.txt /provenance/
WORKDIR /provenance

RUN pip install --no-cache-dir -r requirements.txt
COPY ./provenance.py  /provenance/
RUN  chmod +x provenance.py

ENTRYPOINT ["/provenance/provenance.py"]
