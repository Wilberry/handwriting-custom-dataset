# Handwriting Recognition System with Custom Dataset Support

## Overview

A robust handwriting recognition system that enables users to create and integrate custom datasets for improved model accuracy and user experience. This application provides a flexible platform for training and deploying handwriting recognition models tailored to specific use cases.

## Features

- **Custom Dataset Management**: Upload and manage custom handwriting datasets
- **Flexible Model Training**: Train recognition models on user-defined datasets
- **Enhanced Accuracy**: Improve prediction accuracy by using domain-specific training data
- **RESTful API**: Comprehensive REST API for seamless integration
- **Student and Sample Management**: Organize datasets by students and samples
- **Database Persistence**: Reliable data storage and retrieval

## Project Structure

```
app/
├── main.py                 # Application entry point
├── models.py              # Data models
├── schemas.py             # Request/response schemas
├── database.py            # Database configuration
├── crud.py                # CRUD operations
├── ml.py                  # Machine learning utilities
├── ml_engine.py           # ML engine core functionality
└── routers/
    ├── datasets.py        # Dataset management endpoints
    ├── samples.py         # Sample management endpoints
    └── students.py        # Student management endpoints
uploads/                    # Directory for uploaded files
```

## Requirements

Dependencies are listed in `requirements.txt`. Install them using:

```bash
pip install -r requirements.txt
```

## Getting Started

Refer to the project files for API endpoints and usage instructions.
