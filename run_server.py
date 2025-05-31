"""Small wrapper script to run the FastAPI app."""

import uvicorn

if __name__ == '__main__':
    uvicorn.run('app:app', reload=True)