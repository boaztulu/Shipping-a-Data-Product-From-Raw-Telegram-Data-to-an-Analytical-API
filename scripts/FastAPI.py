from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import select, Session

# Import our database functions and models
from database import engine, create_db_and_tables, get_session
from models import Hero, HeroCreate, HeroPublic

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Hero API",
    description="A simple API for managing heroes with PostgreSQL.",
    version="1.0.0",
)

# --- FastAPI Lifecycle Events ---

@app.on_event("startup")
def on_startup():
    """
    Event that runs when the FastAPI application starts up.
    We use it to create database tables.
    """
    create_db_and_tables()

@app.on_event("shutdown")
def on_shutdown():
    """
    Event that runs when the FastAPI application shuts down.
    You might want to do cleanup here, like closing connection pools,
    though SQLAlchemy's engine handles connections quite well.
    """
    print("Shutting down FastAPI application.")
    # No explicit engine.dispose() is strictly necessary for simple cases
    # as the connection pool will eventually close connections.
    # For more complex scenarios or specific pooling configurations,
    # you might add engine.dispose() here if needed.

# --- API Endpoints ---

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Hero API!"}

@app.post("/heroes/", response_model=HeroPublic, status_code=status.HTTP_201_CREATED)
def create_hero(hero_create: HeroCreate, session: Session = Depends(get_session)):
    """
    Create a new hero.
    """
    db_hero = Hero.from_orm(hero_create) # Convert Pydantic model to SQLModel ORM instance
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero) # Refresh to get the generated ID
    return db_hero

@app.get("/heroes/", response_model=List[HeroPublic])
def read_heroes(
    offset: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """
    Retrieve a list of heroes.
    """
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes

@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(hero_id: int, session: Session = Depends(get_session)):
    """
    Retrieve a single hero by ID.
    """
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@app.put("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(
    hero_id: int,
    hero_update: HeroCreate, # Or a separate HeroUpdate model
    session: Session = Depends(get_session)
):
    """
    Update an existing hero.
    """
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    # Update attributes from the incoming Pydantic model
    for key, value in hero_update.dict(exclude_unset=True).items():
        setattr(hero, key, value)

    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero

@app.delete("/heroes/{hero_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hero(hero_id: int, session: Session = Depends(get_session)):
    """
    Delete a hero by ID.
    """
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    session.delete(hero)
    session.commit()
    return {"message": "Hero deleted successfully"}