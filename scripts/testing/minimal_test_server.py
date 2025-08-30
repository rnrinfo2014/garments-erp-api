#!/usr/bin/env python3
"""
Minimal FastAPI test server to isolate the issue
"""

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Test server is working"}

@app.get("/test")
def test_endpoint():
    return {"status": "ok", "test": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
