## API Configuration

The frontend application connects to a backend API. The base URL for this API can be configured using an environment variable.

Create a file named `.env` in the `frontend` directory (e.g., `frontend/.env`).

In this file, set the `REACT_APP_API_BASE_URL` variable to the full base URL of your backend API.

**Example for local development:**
If your backend is running on `http://localhost:8000`, your `.env` file should contain:
```
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
```

**Example for a deployed server:**
If your backend API is at `https://yourserver.com/api/v1`, your `.env` file should contain:
```
REACT_APP_API_BASE_URL=https://yourserver.com/api/v1
```

If `REACT_APP_API_BASE_URL` is not set, the application will default to `/api/v1` as the base URL, assuming the frontend is served from the same origin as the backend.

**Important:** After creating or modifying the `.env` file, you must restart your frontend development server for the changes to take effect.

## Server-Side CORS Configuration

If your frontend (served from one domain/port) is configured to make API requests to a backend served from a *different* domain or port, you will need to configure Cross-Origin Resource Sharing (CORS) on your backend server. Otherwise, browsers will block these requests for security reasons.

For a FastAPI backend, you can use the `CORSMiddleware`. Here's a basic example of how to add it to your FastAPI application:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",  # Example: your frontend development server
    "https://your-frontend-domain.com", # Example: your deployed frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# ... your other application routes and logic ...
```

Make sure to replace the `origins` list with the actual origins from which your frontend will be making requests.

For more detailed information, refer to the [FastAPI CORS documentation](https://fastapi.tiangolo.com/tutorial/cors/).
