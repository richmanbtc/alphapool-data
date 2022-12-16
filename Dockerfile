FROM jupyter/datascience-notebook:python-3.10.6

USER root

# install required libraries

# RUN apt-get update \
#  && apt-get install -y \
#    libpq-dev

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir \
    ccxt==1.93.98 \
    "git+https://github.com/richmanbtc/ccxt_rate_limiter.git@v0.0.4#egg=ccxt_rate_limiter" \
    "git+https://github.com/richmanbtc/crypto_data_fetcher.git@v0.0.17#egg=crypto_data_fetcher" \
    cloudpickle==2.0.0 \
    'google-cloud-bigquery[bqstorage,pandas]' \
    gql[all] \
    pandas-gbq \
    retry==0.9.2 \
    yfinance \
    quandl \
    pytrends

#dataset==1.5.2 \
#    psycopg2==2.9.3 \

ADD . /app
ENV ALPHAPOOL_LOG_LEVEL=debug
WORKDIR /app
CMD python -m src.main
