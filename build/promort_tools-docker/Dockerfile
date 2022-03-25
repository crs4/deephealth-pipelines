FROM python:3.8

ARG PROMORT_TOOLS_REPO=https://github.com/crs4/promort_tools.git
ARG PROMORT_TOOLS_BRANCH=develop
RUN groupadd promort && useradd -mg promort promort

RUN apt-get update && apt-get install git

ENV HOME=/home/promort

WORKDIR /tmp

USER promort

RUN git clone ${PROMORT_TOOLS_REPO}

WORKDIR /tmp/promort_tools

RUN git checkout ${PROMORT_TOOLS_BRANCH} \
    && pip install --upgrade pip \
    && python setup.py install --user

WORKDIR /home/promort

ENV PATH="/home/promort/.local/bin/:${PATH}"

CMD ["bash"]
