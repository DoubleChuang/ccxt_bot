# CCXT Bot

## How to use

Create a `.env` file, and modify the `LINE_TOKEN` `BINANCE_API_KEY` `BINANCE_SECRET` in the file
```
LINE_TOKEN=YOUR_LINE_TOKEN
BINANCE_API_KEY=YOUR_BINANCE_API_KEY
BINANCE_SECRET=YOUR_BINANCE_SECRET
```

Run from source code
```
poetry install # only needs to be executed once


poetry run python3 ccxt_bot/__main__.py
```

Build docker image from source code
```
docker build -t ccxt_bot .
```



Run image as a container 
```
# Run by self-built Docker image
docker run -d --name ccxt_bot --restart unless-stopped --env-file .env ccxt_bot
# Run by Docker Images built with GitHub Actions
docker run -d --name ccxt_bot --restart unless-stopped --env-file .env ghcr.io/doublechuang/ccxt_bot:1a7815e
```

Ref:
- [poetry venv](https://sean22492249.medium.com/%E5%9C%A8-vscode-%E7%9A%84-poetry-%E6%83%B3%E7%94%A8-python-interpreter-ec5f269b2930)
- [Integrating Python Poetry with Docker](https://stackoverflow.com/questions/53835198/integrating-python-poetry-with-docker)
- [Document docker poetry best practices](https://github.com/python-poetry/poetry/discussions/1879)
- [ccxt python examples](https://github.com/ccxt/ccxt/tree/master/examples/py)
- [schedule doc](https://schedule.readthedocs.io/en/stable/examples.html)