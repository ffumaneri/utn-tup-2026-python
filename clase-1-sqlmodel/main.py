
import logging

from fastapi import FastAPI, Request
from sqlmodel import (
    Session,
    select,
)

from api import login, users
from api.middlewares.check_apikey import CheckApikeyMW
from api.middlewares.counter import CounterMW
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
app.include_router(login.router)

counterMW = CounterMW()
checkApikeyMW = CheckApikeyMW()

@app.middleware("counter")
async def middle_ware_prueba(request: Request, call_next):
    return await counterMW.middle_ware_prueba(request, call_next)

@app.middleware("apikey")
async def middle_ware_apikey(request: Request, call_next):
    return await checkApikeyMW.verify_header_middleware(request, call_next)

def create_dummy_data():
    with Session(database.engine) as session:
        if session.exec(select(UserDB)).first():
            return
        country_names = [("Argentina", 1), ("Brasil", 2)]
        countries = [Country(name=name, id=id) for name, id in country_names]

        session.add_all(countries)
        session.commit()

        names_and_ages = [
            ("Martina Gómez", "mgomez@email.com", 28, 1),
            ("Santiago Fernández", "sfer@email.com", 34, 1),
            ("Valentina López", "vlo@email.com", 22, 1),
            ("Mateo Rodríguez", "mro@email.com", 45, 1),
            ("Camila Martínez", "cma@email.com", 19, 2),
            ("Lucas Pérez", "lpe@email.com", 31, 2),
            ("Sofía García", "sga@email.com", 27, 2),
            ("Nicolás Sánchez", "nsa@email.com", 40, 2),
            ("Julieta Díaz", "jdi@email.com", 24, 2),
            ("Tomás Romero", "tro@email.com", 37, 2),
        ]
        users = [UserDB(name=name, email=email, age=age, country_id=country, password="123") for name, email, age, country in names_and_ages]
        session.add_all(users)
        session.commit()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    create_dummy_data()

