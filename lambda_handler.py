"""
AWS Lambda entry point. API Gateway invokes `handler`.
Keep this file minimal - all real logic lives in app/.
"""
from mangum import Mangum

from app.main import app

handler = Mangum(app)
