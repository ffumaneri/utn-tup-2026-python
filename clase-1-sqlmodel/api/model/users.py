# Nivel de API
from sqlmodel import SQLModel

from model.users import CountryBase


#Nivel API
class CreateUserRequest(SQLModel):
    name: str
    age: int
    country_id: int | None
    password: str

class CreateUserResponse(SQLModel):
    id: int

class CountryResponse(CountryBase):
    id: int

class GetUsersResponse(SQLModel):
    id: int
    name: str

class GetUserResponseWithCountry(GetUsersResponse):
    age: int
    password: str | None
    country: CountryResponse | None = None