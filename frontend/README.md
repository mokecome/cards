## API Configuration

The frontend application connects to a backend API. The base URL for this API can be configured using an environment variable. This configuration method is the definitive way to set the API endpoint for **production builds** (`npm run build`). For local development, the `proxy` setting in `package.json` (detailed in the "Development Proxy" section) also plays a role, but it is **not** used in production.

To set the API endpoint for production, or to override the development proxy with a specific URL during development, create a file named `.env` in the `frontend` directory (e.g., `frontend/.env`).

In this file, set the `REACT_APP_API_BASE_URL` variable to the full base URL of your backend API. This variable is read during the build process for production or when the development server starts.

**Example for local development (overriding proxy or for specific backend):**
If your backend is running on `http://localhost:8000`, your `frontend/.env` file should contain:
```
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
```

**Example for a deployed server (production build):**
If your backend API is at `https://yourserver.com/api/v1`, your `frontend/.env` file (or the environment variable set in your deployment environment) should be:
```
REACT_APP_API_BASE_URL=https://yourserver.com/api/v1
```

If `REACT_APP_API_BASE_URL` is not set (either via `.env` file or an environment variable during the build process for production), the application will default to `/api/v1`. This implies the frontend application is served from the same domain and port as the backend API.

**Important:** After creating or modifying the `.env` file, you must restart your frontend development server for the changes to take effect. Production builds will use the value present at the time of the build.

## Development Proxy

During development (when using `npm start` or `yarn start`), this Create React App project uses a proxy to forward API requests if `REACT_APP_API_BASE_URL` is not set to an absolute URL. This is configured in the `package.json` file:

```json
"proxy": "http://localhost:8006"
```

**How it interacts with `REACT_APP_API_BASE_URL`:**

1.  **If `REACT_APP_API_BASE_URL` is NOT set in your `frontend/.env` file, OR if it's set to a relative path (e.g., `/api/v1` which is the default behavior without an env var):**
    *   API calls made by the frontend (e.g., to `/api/v1/cards`) will be intercepted by the development server.
    *   The development server will then forward these requests to the URL specified in the `proxy` setting. For example, a request to `/api/v1/cards` becomes `http://localhost:8006/api/v1/cards`.
    *   This is useful for avoiding CORS issues during development if your backend API server is running on `http://localhost:8006`.

2.  **If `REACT_APP_API_BASE_URL` IS set to an ABSOLUTE URL in your `frontend/.env` file (e.g., `REACT_APP_API_BASE_URL=http://my-custom-backend.com/api/v1`):**
    *   API calls will be made directly to this absolute URL.
    *   The `proxy` setting in `package.json` will be bypassed by the development server for these direct API calls.
    *   This is useful if your development backend is running on a different machine or port not covered by the proxy, or if you want to test against a staged/remote backend.

Remember to restart your development server after making changes to `.env` files or `package.json`.

## Server-Side CORS Configuration

If your frontend (served from one domain/port) is configured to make API requests to a backend served from a *different* domain or port (especially when `REACT_APP_API_BASE_URL` is an absolute URL or in production when frontend and backend are on different origins), you will need to configure Cross-Origin Resource Sharing (CORS) on your backend server. Otherwise, browsers will block these requests for security reasons.

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
