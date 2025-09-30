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
git clone https://github.com/YOUR_USERNAME/pg-device-api.git
cd pg-device-api

# Create environment
conda create -n medical-device python=3.11 -y
conda activate medical-device

# Install dependencies
pip install -r requirements.txt

# Run server
python app/run_dev.py
