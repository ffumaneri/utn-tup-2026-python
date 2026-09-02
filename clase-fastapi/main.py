from fastapi import FastAPI, status, HTTPException
from models.users import User, GetUsersResponse, CreateUserResponse, DeleteUserResponse

# Create the application instance
app = FastAPI()


usuarios = [
    {"id": 1, "name": "juan perez"},
    {"id": 2, "name": "pepe sanchez"}
]

# Define a GET route for the root URL
@app.get("/")
def read_root():
    mensaje = "Primer clase de FastAPI"
    return {"message": mensaje}

@app.get("/user")
def get_users() -> GetUsersResponse:
    r = GetUsersResponse(users = usuarios)
    return r

@app.delete("/user/{id}")
def delete_user(id: int) -> DeleteUserResponse:
    for user in usuarios:
        if user["id"] == id:
            usuarios.remove(user)
            return {"message" : "ususario borrado"}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="Usuario no encontrado"
    )

@app.post("/user")
def create_user(user: User) -> CreateUserResponse:
    usuarios.append(user)
    return {"message": "usuario creado"}