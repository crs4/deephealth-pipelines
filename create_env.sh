#!/usr/bin/env bash
set -xe

echoerr() { echo "$@" 1>&2; }

if [ ! -f .env ]; then
  sed  "s|AIRFLOW_HOME_PLACEHOLDER|$(pwd)/data|g" env.template > .env
else
   echoerr ".env found, skip creation"
fi

source .env

if [ ! -f promort_config/config.yaml ]; then
  cp promort_config/config.yaml.template promort_config/config.yaml
  sed  -i "s|PROMORT_DB|${PROMORT_DB}|g" promort_config/config.yaml
  sed  -i "s|PROMORT_USER|${PROMORT_USER}|g" promort_config/config.yaml
  sed  -i "s|PROMORT_PASSWORD|${PROMORT_PASSWORD}|g" promort_config/config.yaml
  sed  -i "s|PROMORT_SESSION_ID|${PROMORT_SESSION_ID}|g" promort_config/config.yaml
else
   echoerr "promort conf found, skip creation"
fi

mkdir -p $PREDICTIONS_DIR
chmod a+w $PREDICTIONS_DIR

mkdir -p $INPUT_DIR
chmod a+w $INPUT_DIR

mkdir -p $FAILED_DIR
chmod a+w $FAILED_DIR

mkdir -p $BACKUP_DIR
chmod a+w $BACKUP_DIR

python -c "\
import toml
dependencies = toml.load(open('pyproject.toml'))['tool']['poetry']['dependencies']

cw_airflow = dependencies.pop('cwl-airflow')
git_repo = cw_airflow['git']
rev = cw_airflow['rev']
print(f'CWL_AIRFLOW_VERSION={rev}')
print(f'CWL_AIRFLOW_URL={git_repo}')

dependencies.pop('python')
extra_pip_deps = []
for k, v in dependencies.items():
  extra_pip_deps.append(f'{k}=={v.strip(\"^\")}')
print(f'EXTRA_PIP_DEPS={\" \".join(extra_pip_deps)}')
" >> .env
source .env

CWL_AIRFLOW_DIR=build/cwl-airflow
if [ ! -d $CWL_AIRFLOW_DIR ]; then
  git clone $CWL_AIRFLOW_URL --branch $CWL_AIRFLOW_VERSION $CWL_AIRFLOW_DIR
else
   echoerr "cwl aiflow found, skip cloning"
fi

