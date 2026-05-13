from fastapi import APIRouter
from app.api.v1.endpoints import products, search, chat, cart, recommendations, users

api_router = APIRouter()
api_router.include_router(products.router)
api_router.include_router(search.router)
api_router.include_router(chat.router)
api_router.include_router(cart.router)
api_router.include_router(recommendations.router)
api_router.include_router(users.router)
