
from fastapi import FastAPI
from sqlmodel import (
    Session,
    select,
)

from api import users
from api.users import User
from data import database
from data.database import create_db_and_tables
from model.users import Country

app = FastAPI()
app.include_router(users.router)

def create_dummy_data():
    with Session(database.engine) as session:
        if session.exec(select(User)).first():
            return
        country_names = [("Argentina", 1), ("Brasil", 2)]
        countries = [Country(name=name, id=id) for name, id in country_names]

        session.add_all(countries)
        session.commit()

        names_and_ages = [
            ("Martina Gómez", 28, 1),
            ("Santiago Fernández", 34, 1),
            ("Valentina López", 22, 1),
            ("Mateo Rodríguez", 45, 1),
            ("Camila Martínez", 19, 2),
            ("Lucas Pérez", 31, 2),
            ("Sofía García", 27, 2),
            ("Nicolás Sánchez", 40, 2),
            ("Julieta Díaz", 24, 2),
            ("Tomás Romero", 37, 2),
        ]
        users = [User(name=name, age=age, country_id=country) for name, age, country in names_and_ages]
        session.add_all(users)
        session.commit()
        
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    create_dummy_data()

