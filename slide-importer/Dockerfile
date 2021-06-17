FROM python:3.6

ENV PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /opt/slide_importer
COPY poetry.lock pyproject.toml  /opt/slide_importer/
COPY slide_importer /opt/slide_importer/slide_importer
RUN python -m pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction 


ENTRYPOINT ["python", "slide_importer/local.py"]

