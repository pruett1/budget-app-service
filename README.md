# **budget-app-service**

## Build
Ensure that pip is installed and then run ```pip install -e .```

### Manual Setup
Add configuration files (env/env_name.json and keys.py)

#### **env_name.json**
```json
{
    "plaid": {
        "CLIENT_ID": "your_plaid_client_id",
        "SECRET": "your_plaid_secret"
    },
    "session": {
        "SECRET_KEY": "secret_key_for_session_encoding",
        "DURATION_SECONDS": 3600, // duration JWT lasts for
        "HEADER": {
            "algorithm": "your_preferred_algorithm",
            "typ": "example"
        },
        "CLEANUP_INTERVAL_SECONDS": 600 // set cleanup interval
    },
    "db": {
        "URI": "uri_to_mongodb",
        "DB_NAME": "mongodb_name"
    }
}
```

#### **keys.py**
```python
secret_key = b"32_byte_key_for_encryption"
```

#### **Helper functions**
Add envs.py with the function Env that returns proper config file

Add src.helpers.encryption with the functions pwd_hash, encrypt, and decrypt (look at test.helpers.encryption for expected behavior)

## Run

### Tests
- To just run unit tests simply run ```pytest```
- To get code coverage run ```coverage run -m pytest``` followed by ```coverage report```

### Local
Ensure mongodb is installed and running with ```mongod``` and that it is listening on port _27017_

```uvicorn src.app:app --reload --log-level debug``` (this defaults to listening on localhost port _8000_)