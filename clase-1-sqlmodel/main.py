
import logging
import time

from fastapi import FastAPI, Request
from sqlmodel import (
    Session,
    select,
)

from api import users
from api.users import UserDB
from model.users import Country
from repositories import database
from repositories.database import create_db_and_tables

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

app = FastAPI()
app.include_router(users.router)

@app.middleware("prueba")
def middle_ware_prueba(request: Request, call_next):
    start_time = time.perf_counter()
    response = call_next(request)
    process_time = time.perf_counter() - start_time
    logger.info(f"process time {str(process_time)}")
    return response

def create_dummy_data():
    with Session(database.engine) as session:
        if session.exec(select(UserDB)).first():
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
        users = [UserDB(name=name, age=age, country_id=country) for name, age, country in names_and_ages]
        session.add_all(users)
        session.commit()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    create_dummy_data()

