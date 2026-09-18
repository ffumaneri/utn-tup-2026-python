from typing import Annotated

from fastapi import Depends

from repositories.users import UserRepository
from services.users import UserService, UserServiceInterface


UserServiceDep = Annotated[UserServiceInterface, Depends(UserService)]
