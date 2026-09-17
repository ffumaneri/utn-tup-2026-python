# Se define el modelo

# Nivel de negocios
from sqlmodel import Field, Relationship, SQLModel


class CountryBase(SQLModel):
    name: str = Field(index=True)

#Nivel de DB
class Country(CountryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    users: list["UserDB"] = Relationship(back_populates="country")
    

# Nivel de negocio 
class User(SQLModel):
    name: str = Field(index=True)
    age: int
    country_id: int | None = Field(default=None, foreign_key="country.id")
    password: str | None = Field(default=None)

# Nivel de base de datos
class UserDB(User, table=True):
    id: int | None = Field(default=None, primary_key=True)
    country: Country | None = Relationship(back_populates="users")
