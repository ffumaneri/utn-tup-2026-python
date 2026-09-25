# Nivel de API
from sqlmodel import SQLModel

from model.users import CountryBase


#Nivel API
class CreateUserRequest(SQLModel):
    name: str
    age: int
    country_id: int | None
    email: str
    password: str

class CreateUserResponse(SQLModel):
    id: int

class CountryResponse(CountryBase):
    id: int

class GetUsersResponse(SQLModel):
    id: int
    name: str

class DeleteUserResponse(SQLModel):
    msg: str

class GetUserResponseWithCountry(GetUsersResponse):
    age: int
    email: str
    country: CountryResponse | None = None