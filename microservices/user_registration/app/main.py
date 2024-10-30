from fastapi import FastAPI
from .db import engine, Base
from .routes import user

# Create database tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app = FastAPI(on_startup=[init_db])

# Include the user routes
app.include_router(user.router, prefix="/users")
