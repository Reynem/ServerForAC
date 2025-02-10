from datetime import timedelta
from dependencies import get_db
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from hashpass import hash_password, verify_password
from models import User
from security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, decode_access_token
from fastapi import Header
from security import get_current_user
import model


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdateName(BaseModel):
    new_name: str


app = FastAPI()


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

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "user_id": db_user.id}

@app.get("/get_user")
async def get_user(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return {"name": user.name, "email": user.email}


@app.put("/update_name")
async def update_name(
    update_data: UserUpdateName,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    user_id = int(payload.get("sub"))

    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.name = update_data.new_name
    await db.commit()
    await db.refresh(db_user)

    return {"message": "Name updated successfully", "new_name": db_user.name}

app.include_router(model.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)