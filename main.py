import random

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
from hashpass import hash_password, verify_password
from database import SessionLocal
from models import User


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


app = FastAPI()


async def get_db():
    async with SessionLocal() as db:
        yield db


@app.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user.email))
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(name=user.name, email=user.email, password=hash_password(user.password))
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}


@app.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user.email))
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    return {"message": "Login successful", "user_id": db_user.id}


@app.post("/predict")
async def predict(image: UploadFile = File(...)):
    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    result = random.randint(1, 100)

    return {"result": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)