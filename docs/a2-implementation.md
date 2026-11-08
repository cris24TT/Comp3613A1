# Assignment 2 Implementation

## Repository

https://github.com/cris24TT/Comp3613A1

## API Routes

### `app/routers/api.py`

| Method | URL | Allowed role | Purpose | Success code | Error codes |
|---|---|---|---|---:|---|
| POST | `/api/login` | Public | Authenticate a user and return an access token. | 200 | 401 |
| GET | `/api/positions` | Student | List open internship positions, optionally filtered by search text. | 200 | 401, 403 |
| GET | `/api/applications` | Student | List the signed-in student's applications. | 200 | 401, 403 |
| GET | `/api/applications/{application_id}` | Student | View one of the signed-in student's applications and status history. | 200 | 401, 403, 404 |
| POST | `/api/applications` | Student | Submit an internship application with a résumé and cover letter. | 201 | 400, 401, 403 |
| GET | `/api/review/applications` | Coordinator | List applications assigned to the signed-in coordinator. | 200 | 401, 403 |
| GET | `/api/review/applications/{application_id}` | Coordinator | View an assigned application and its status history. | 200 | 401, 403, 404 |
| PATCH | `/api/review/applications/{application_id}/status` | Coordinator | Change an assigned application's status with a required reason. | 200 | 400, 401, 403 |

### `app/routers/users.py`

| Method | URL | Allowed role | Purpose | Success code | Error codes |
|---|---|---|---|---:|---|
| GET | `/api/users` | Admin | List all users. | 200 | 401 |

## Tests and Postman Collection

Unit tests live in `tests/unit`. Run them with:

```text
python manage.py test unit
```

Integration tests live in `tests/integration`. Run them with:

```text
python manage.py test integration
```

The Postman collection is at
`postman/internship-portal.postman_collection.json`. Import it into Postman,
set the `baseUrl` collection variable, and run it with the Collection Runner.

## Project Description

The Internship Application Portal lets students apply for internships. Each
application is automatically assigned to a coordinator in the position's
department. Coordinators can accept, deny, or revoke applications and must
provide a reason for each decision. Students can track their application status
and view the reason recorded by the coordinator.
