"""AWS Lambda entry point (Mangum wraps FastAPI)."""
from mangum import Mangum
from server import app

handler = Mangum(app, lifespan="on")
