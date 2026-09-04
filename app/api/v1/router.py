from fastapi import APIRouter

from app.api.v1 import auth, media, persons, relationships, tree

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(persons.router)
api_router.include_router(relationships.router)
api_router.include_router(tree.router)
api_router.include_router(media.router)
