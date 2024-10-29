#!/bin/bash

# Script Name: db_reset.sh
# Description: Reset the database to its initial state

alembic downgrade base && \
rm -rf app/db/migrations/versions/* && \
alembic revision --autogenerate -m "Initial migration" && \
alembic upgrade head