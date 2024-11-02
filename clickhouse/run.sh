#!/bin/bash

# Directory containing SQL files
SQL_DIR="./sql"

# ClickHouse server details
CLICKHOUSE_HOST="49.13.127.227"
CLICKHOUSE_PORT="9000"
CLICKHOUSE_USER="default"
CLICKHOUSE_PASSWORD="*****"
CLICKHOUSE_DATABASE="default"

# Function to execute SQL file
execute_sql_file() {
    local sql_file=$1
    echo "Executing $sql_file..."
    clickhouse client --host=$CLICKHOUSE_HOST --port=$CLICKHOUSE_PORT --user=$CLICKHOUSE_USER --password=$CLICKHOUSE_PASSWORD --progress 1 --database=$CLICKHOUSE_DATABASE --query="$(cat $sql_file)"
}

# Iterate over all SQL files in the directory, sort them, and execute them
for sql_file in $(ls $SQL_DIR/*.sql | sort); do
    if [ -f "$sql_file" ]; then
        execute_sql_file "$sql_file"
    else
        echo "No SQL files found in $SQL_DIR"
    fi
done
