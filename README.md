# PiroGon Device API

Open-source medical device data management system.

## Features

- Patient management
- Therapy session tracking
- Signal data storage (ECG, EMG, Impedance)
- REST API with OpenAPI documentation
- JWT authentication
- Audit logging

## Quick Start

```bash
# Clone repository
git clone https://github.com/PiroGon-Dev/x-phagia-api.git
cd x-phagia-api

# Create environment
conda create -n medical-device python=3.11 -y
conda activate medical-device

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000   
```
