# Se define el modelo

# Nivel de negocios
from sqlmodel import Field, Relationship, SQLModel


class CountryBase(SQLModel):
    name: str = Field(index=True)

#Nivel de DB
class Country(CountryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    users: list["User"] = Relationship(back_populates="country")


# Nivel de negocio 
class UserBase(SQLModel):
    name: str = Field(index=True)
    age: int
    country_id: int | None = Field(default=None, foreign_key="country.id")
    password: str | None = Field(default=None)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    country: Country | None = Relationship(back_populates="users")
