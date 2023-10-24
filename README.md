# YouTube Data Project
End-to-end data science pipeline which uses Youtube data

## Tools used as part of this project:
1. YouTube Data API
2. Python
3. SQL
4. Docker
5. Google Cloud:
    - Google BigQuery
    - Google Cloud Storage
    - Service accounts
    - Artifact Repository (Container Registry)
    - Monitoring
6. Hugging Face Transformers
7. Makefiles
8. Python Virtual Environments
9. Jupyter Notebooks
10. Google Looker Studios
11. Linting (flake8)
12. Git Commit Hooks


## Setup

1.) Setup environment for running the code. It would create a python enviroment with the name `yt-env`
```
make env
```

2.) After the environment is created, activate it by following make command
```
source yt-env/bin/activate
```

3.) Set environment variable for Youtube API key
```
export YOUTUBE_API_KEY=<your-api-key>
```

4.) If you want to use service account, you need to put the value of secret key in an environment variable. Below, we are reading the key from `../service-account.json`.
```
export SERVICE_ACCOUNT_SECRET_KEY=$(cat ../service-account.json)
```

NOTE: You would need to install PyTorch, which I did using the following command since I am running on CPU.
If you want to have a different config for PyTorch, please see [this](https://pytorch.org/get-started/locally/)


## Setup for Jupter Notebook
If you want to use jupyter notebook:
```
make env-notebook

python -m ipykernel install --user --name=yt-venv-jupyter
```

Apart from the above, you will need to install `docker` to build and push docker images.

## Docker Build and Run

We have the following make commands to build, push and run docker containers

```
make docker-build
make docker-push
make docker-run
```

## Linting and Githooks

To setup linting with githooks, add the file `.git/hooks/pre-commit` with folllowing contents:

```
#!/usr/bin/env bash

# Get the list of changed files.
changed_files=$(git diff --name-only HEAD | grep -E '\.py$')

# If there are any changed Python files, run Flake8.
if [[ $changed_files ]]; then
  flake8 --ignore=E501 $changed_files
fi
```

To run linting, run the following:

```
make lint
```

## Resources

- [Looker Dashboard](https://lookerstudio.google.com/u/0/reporting/c51cf45f-b415-48a9-8f48-0f95be95a616/page/tEnnC)




