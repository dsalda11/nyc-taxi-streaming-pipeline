#!/bin/bash


DATASET_URL="https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-03.parquet"
TARGET_PATH="/cse511/yellow_tripdata_2022-03.parquet"
echo "Downloading dataset..."
wget -O "$TARGET_PATH" "$DATASET_URL"

if [ $? -eq 0 ]; then
    echo "Download complete: $TARGET_PATH"
else
    echo "Download failed!" >&2
    exit 1
fi
