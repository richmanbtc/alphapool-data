## alphapool-data

rules

- hourly
- depends data before timestamp + interval

## local dev

```bash
docker-compose run fetcher bash
```

install gcloud to auth
https://cloud.google.com/sdk/docs/install?#deb

```bash
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | tee /usr/share/keyrings/cloud.google.gpg && apt-get update -y && apt-get install google-cloud-sdk -y
```

```bash
gcloud auth application-default login
```

```bash
python -m src.main
```
