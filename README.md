# FastAPI-MongoDB Project
This is a FastAPI project that uses MongoDB as the database and pymongo as the connector. The project provides REST API endpoints for managing users, organizations, and permissions.

## Tech Stack

- Python-FastAPI
- MongoDB
- pymongo

## Database Collections

The project uses the following collections in the MongoDB database:

- `users` with fields `id`, `name`, and `email`
- `orgs` with fields `id` and `name`
- `permissions` with fields `user_id`, `org_name`, and `role`

## Endpoints

The following endpoints are available:

### Users

- `GET /users`: Returns a list of users, with optional filtering by name.
- `GET /users/{user_id}`: Returns the details of a specific user.
- `POST /users`: Creates a new user.

### Orgs

- `GET /orgs`: Returns a list of organizations, with optional filtering by name.
- `POST /orgs`: Creates a new organization.

### Permissions

- `POST /permissions`: Creates/Updated new permissions in bulk.
- `DELETE /permissions`: Deletes permissions in bulk.

## Bulk Operations

The `POST /permissions` and `DELETE /permissions` endpoints are designed to allow for bulk creation/updating and deletion of permissions, respectively.

## Live API Documentation

The live API documentation is available at the `/docs` endpoint.

## Installation

1. Clone the repository.
2. Install the required dependencies using `pip install -r requirements.txt`.
3. Start the FastAPI server using `uvicorn main:app --reload`.

## Conclusion

This project demonstrates the use of FastAPI and MongoDB together to create a powerful and efficient REST API. 