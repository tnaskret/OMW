# Open Multilingual Wordnet 2.0

## Dependencies
(for ubuntu)
    - [docker](https://docs.docker.com/install/)
    - [docker-compose](https://docs.docker.com/compose/install/)

 ## Installation
    - run `./build.sh` to build docker image and prepare database;

 ## Start application
    - run `./start.sh`

## For Development
   - Requires Python 3
   - `pip3 install -r requirements.txt`
   - `pip3 install --editable .`
   - `omw db_init reset`
   - `omw db_load load_all`
   - `omw db_update update_all`
   - `gunicorn -b 0.0.0.0:5000 --access-logfile - "omw.app:create_app()"`

