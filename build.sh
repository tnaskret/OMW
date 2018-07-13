#!/bin/bash

docker-compose down
docker-compose build
docker-compose run website omw db_init reset
docker-compose run website omw db_load load_all
docker-compose run website omw db_update update_all
docker-compose down