curl --location --request POST 'http://localhost:8018/optimisations/' \
--header 'x-api-key: foo' \
--header 'Content-Type: application/json' \
--data-raw '{
    "asset_name": "solar",
    "datetime": "2023-03-22T09:00:00",
    "power": 72.3
}'