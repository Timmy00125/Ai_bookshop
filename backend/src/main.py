from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .routers import admin, ai, auth, books, cart, orders, users

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-Enhanced Online Bookshop", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(ai.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(users.router)
app.include_router(admin.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the AI-Enhanced Online Bookshop API"}
