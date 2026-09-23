from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from repositories.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]

from repositories.users import UserRepository  # noqa: E402

UserRepositoryDep = Annotated[UserRepository, Depends(UserRepository)]

from services.users import UserService, UserServiceInterface  # noqa: E402

UserServiceDep = Annotated[UserServiceInterface, Depends(UserService)]
