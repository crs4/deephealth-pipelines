FROM python:3-stretch

COPY ./ /prov_crate
WORKDIR /prov_crate

RUN pip install --no-cache-dir -r requirements.txt && \
    chmod +x gen_crate.py

ENTRYPOINT ["/prov_crate/gen_crate.py"]
