# E-Commerce Backend Flask Rest-API

A scalable e-commerce backend API built with Flask(blueprint setup), MongoEngine, Celery, and Redis. Supports user authentication, product management, cart systems, order processing, coupon management, caching, input validation(using masrshmallow)and rate limiting.

![Tech Stack](https://img.shields.io/badge/tech-flask%20%7C%20mongodb%20%7C%20celery%20%7C%20redis-blue)

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Technologies](#technologies)
- [Setup and Installation](#setup-and-installation)
- [API Endpoints](#api-endpoints)
- [Scalability Considerations](#scalability-considerations)
- [Postman Collection](#postman-collection)
- [Future Improvements](#future-improvements)
- [License](#license)

## Overview
This backend API powers an e-commerce platform with JWT authentication, role-based access control, and asynchronous task processing. It integrates MongoDB for data storage, Redis for caching and message brokering, and Celery for background tasks like order notifications. Designed for scalability, it includes input validations, rate limiting and Redis caching to optimize performance.

## Features

### User Authentication
- JWT-based authentication (access and refresh tokens).
- User registration and login.
- Role-based access control (Admin/Customer).

### Product Management
- **CRUD operations** for products (Admin-only creation/editing/deleting).
- Support for product categories, stock tracking, images, and variants.
- Public endpoints for browsing products.

### Cart System
- Persistent cart storage per user.
- Add/remove items and update quantities.
- Automatic cart clearance after order placement.

### Order Processing
- Convert cart items into orders.
- Track order status: `Pending` → `Shipped` → `Delivered`.
- Celery-powered email notifications for order updates.

### Discount & Coupon System
- Admin-only coupon creation with expiry dates.
- Role-based coupon eligibility (e.g., exclusive discounts for customers or prime users).
- Coupon validation during checkout.

## Technologies
- **Flask**: Python web framework for building API endpoints.
- **MongoEngine**: MongoDB ODM for data modeling and queries.(**why MongoEngine over PyMongo**: MongoEngine provides ODM abstraction (schema enforcement, Pythonic queries, relationships) vs PyMongo’s low-level driver, streamlining MongoDB interactions in Flask.)
- **Celery**: Asynchronous task queue (e.g., sending order emails).
- **Redis**: Caching frequently accessed data and Celery message brokering.
- **Flask-JWT-Extended**: Secure JWT token management.
- **Flask-Limiter**: Rate limiting to prevent API abuse.
- **Docker**: Containerization for seamless deployment.

## Setup and Installation
### Prerequisites
- Python 3.9+
- MongoDB
- Redis
- Docker (optional, for containerization)
### Local Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/vn33/E-Commerce-Backend-Flask-Rest-API.git
   cd ecommerce-api
   ```
2. **Create a virtual environment and install dependencies**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # For Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
3. **Create config.py file (follow path: ecommerce-api/config.py)**:
Add the following settings to your **config.py** file, ensuring sensitive values are stored securely (e.g., environment variables in production):
    ```python
    # config.py
    import os

    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')  # Replace with a secure key in production
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ecommerce')  # MongoDB connection URI
    FLASK_JWT_SECRET_KEY = os.getenv('FLASK_JWT_SECRET_KEY', 'secret_key')  # JWT token signing key (use env vars in prod)
    CACHE_TYPE = "RedisCache"  # Redis for caching
    CELERY_BROKER_URL = "redis://localhost:6379/0"  # Production Redis broker URL (omit in debug mode)
    ```
4. **Run the Flask Application:**:
    ```bash
       python run.py
    ```

## API Endpoints
### User Authentication
- **Register**: `POST /auth/register`
**input validations using Marshmallow**
Payload:
    ```json
    {
        "email": "user@example.com",
        "password": "securePassword123",
        "role": "customer"  // Options: customer, admin, prime_customer
    }
    ```
- **Login**: `POST /auth/login`
Payload:
    ```json
    {
        "email": "user@example.com",
        "password": "securePassword123"
    }
    ```
    Returns access and refresh tokens.

- **Refresh Access Token**: `GET /auth/refresh_access_token`
Getting new access token from refresh token and revoking the old access token(storing in database)
- **Protected Auth**: `GET /auth/protected`
Getting user info from jwt access token.
- **Logout**: `GET /auth/logout`

### Product Management
- **Fetch All Products**: `GET /products/all_products`
Supports pagination via query parameters: page and per_page.
- **Create Product (Admin Only)**: `POST /products/create_product`
Payload:
    ```json
    {
        "name": "Smart Watch X",
        "description": "Feature-packed smart watch with heart rate monitor and GPS.",
        "category": "Wearables",
        "images": [
            "https://example.com/images/smartwatch-x.jpg"
        ],
        "variants": [
            {
            "sku": "SWX-001",
            "stock": 60,
            "price": "129.99"
            }
        ]
    }
    ```
- **Update Product (Admin Only)**: `PUT /products/update_product/<product_id>`
- **Read Product**: `GET /products/<product_id>`
- **Delete Product (Admin Only)**: `DELETE /products/delete_product/<product_id>`

### Cart System
- **Get Cart**: `GET /cart/details` (uses JWT identity to fetch the cart)
- **Add Item to Cart**: `POST /cart/add_item` 
Payload:
    ```json
    {
        "product_id": "67eba24773b2de600ddd7b5e",
        "quantity": 2,
        "price": "29.99"  //optional: If price is not provided, it will be fetched from the Product model
    }
    ```
- **Remove Item from Cart**: `POST /cart/remove_item`
- **Update Quantity**: `POST /cart/update_item_quantity`

### Order Processing
- **Create Order**: `POST /orders/create` 
This endpoint fetches items from the cart. Payload:
    ```json
    {
        "coupon_code": "DISCOUNT10"  // Optional
    }
    ``
- **Track Order**: `GET /orders/<order_id>`

### Discount & Coupon System
- **Apply Coupon**: `GET /coupons/my_coupons` (uses JWT identity to fetch the available coupons as per role)
- **Create Coupon (Admin Only)**: `POST /coupons/create` 
Payload:
    ```json
    {
        "code": "DISCOUNT10",
        "discount_percent": 10,
        "expiry": "2025-12-31T23:59:59",
        "eligible_roles": ["customer", "prime_customer"]
    }
    ```
- **Update Coupon (Admin Only)**: `PUT /coupons/update/<coupon_code>` 
Payload:
    ```json
    {
    "discount_percent": 15,
    "expiry": "2026-01-31T23:59:59",
    "eligible_roles": ["prime_customer"]
    }
    ```
- **Delete Coupon (Admin Only)**: `DELETE /coupons/delete/<coupon_code>`
- **Get All Coupons (Admin Only)**: `GET /coupons/all`

## Scalability Considerations
- **Database**
  - ***MongoDB***: Used as the primary database for storing product, user, and order data.
  - ***Indexing***: Proper indexing is applied to optimize query performance.
  - ***Pagination***: Implemented in API responses to reduce load and improve efficiency.

- **Redis Caching**
  - Uses ***Redis*** to cache frequently accessed data (e.g., product lists) to reduce MongoDB load and improve API response times.
  - Cached responses for APIs such as `/all_products` ensure faster retrieval without hitting the database on every request.

- **Rate Limiting**
  - **Flask-Limiter** is integrated to prevent API abuse.
  - Global rate limits are enforced (e.g., **10 requests per minute**) with the possibility to override per route.
  - Helps prevent excessive database queries by limiting unnecessary API calls.

- **Background Tasks**
  - ***Celery*** is used to handle long-running tasks asynchronously.
  - Example: Sending order notifications happens in the background, ensuring a smoother user experience while reducing API response time.
  - Uses **Redis** as the message broker to queue and process background tasks efficiently.

## Postman Collection
A Postman collection is provided to facilitate testing and exploration of the API endpoints. This collection includes all api endpoints.

## Future Improvements
- Implement GraphQL API for more flexible data fetching. 
- Add WebSockets for real-time order tracking. 
- Create a basic admin panel for managing orders and users. 
- Integrate a payment gateway for secure transactions(stripe).
- Implement a search feature for products using Elasticsearch.
- Expand background task capabilities (e.g., integration with external email/SMS providers).
- Dockerize Application.
- Deploy APIs on AWS with CI/CD setup.

## License
This project is licensed under the MIT License. See the LICENSE file for details.