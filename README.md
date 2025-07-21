# HROne_Backend_Task
E-commerce API
This project is a robust and scalable E-commerce API built with FastAPI, designed to manage products and customer orders. It provides a set of RESTful endpoints for common e-commerce operations, backed by a MongoDB database for efficient data storage.

Features
Product Management:

Create new products with details like name, price, size, and description.

List all products with optional filtering by name and size, and pagination.

Order Management:

Create new orders, including multiple products and quantities, with automatic total amount calculation.

Retrieve a user's order history with pagination.

Health Check: An endpoint to verify the API's operational status and database connectivity.

Scalable & Asynchronous: Built with FastAPI and motor (asynchronous MongoDB driver) for high performance.

Technologies Used
FastAPI: A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.

Pydantic: Used for data validation and settings management.

Uvicorn: An ASGI server for running FastAPI applications.

Motor: An asynchronous Python driver for MongoDB.

PyMongo: The official MongoDB driver for Python (often a dependency of Motor).

python-dotenv: For managing environment variables during local development.

MongoDB: A NoSQL database used for data persistence.

Local Setup
Follow these steps to get the API running on your local machine.

Prerequisites
Python 3.12 (or compatible version)

pip (Python package installer)

Git

MongoDB instance (local or remote, e.g., MongoDB Atlas)

Deployment
This application can be easily deployed to platforms like Render.

Live Application Link:
hronebackendtask-production.up.railway.app

