

################################################################
# BASE
################################################################
FROM python:3.11.1 as base
# FROM python:3.11.1-slim as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # poetry
    # https://python-poetry.org/docs/configuration/#using-environment-variables
    POETRY_VERSION=1.4.0 \
    # make poetry install to this location
    POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
    \
    # paths
    # this is where our requirements + virtual environment will live
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        wget \
    && rm -rf /var/lib/apt/lists/*

# TA-Lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
  tar -xvzf ta-lib-0.4.0-src.tar.gz && \
  cd ta-lib/ && \
  ./configure --prefix=/usr --host=$(if [ $(uname -m|grep x86) ]; then echo "x86"; else echo "arm"; fi) && \
  make && \
  make install

RUN apt-get purge -y --auto-remove \
    gcc \
    wget

RUN rm -R ta-lib ta-lib-0.4.0-src.tar.gz

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

################################################################
# BUILDER
################################################################

FROM base as builder
WORKDIR $PYSETUP_PATH

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.4.0

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock README.md ./
COPY ccxt_bot ./ccxt_bot

COPY .git ./.git
RUN sed -i "s/__commit_hash__.*/__commit_hash__ = '$(git rev-parse --short HEAD)'/g" $PYSETUP_PATH/ccxt_bot/__init__.py && \
    rm -rf ./.git

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        wget \
    && rm -rf /var/lib/apt/lists/*

RUN poetry config virtualenvs.in-project true && \
    poetry install --only=main --no-root \
    && poetry build

RUN apt-get purge -y --auto-remove \
    gcc \
    wget

RUN rm -rf ./ccxt_bot \
    pyproject.toml \
    poetry.lock \
    README.md

################################################################
# PRODUCTION
################################################################

FROM base as final

COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH
RUN pip install $PYSETUP_PATH/dist/*.whl && rm -rf $PYSETUP_PATH/dist

CMD ["python3", "-m", "ccxt_bot"]