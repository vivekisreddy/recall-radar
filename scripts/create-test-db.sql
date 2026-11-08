-- Runs once when the Postgres container is first created: a separate database for `make test`.
CREATE DATABASE recall_radar_test OWNER recall;
