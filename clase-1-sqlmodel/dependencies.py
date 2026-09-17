# isort: skip_file
# NOTE: imports below are intentionally interleaved with the alias definitions,
# not grouped at the top. repositories/users.py and services/users.py import
# their Dep alias back from this module, so each alias must be defined before
# the module that needs it is imported, or the circular import breaks. Do not
# let an auto-import-sort tool flatten this back to top-of-file imports.
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from repositories.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]

from repositories.users import UserRepository

UserRepositoryDep = Annotated[UserRepository, Depends(UserRepository)]

from services.users import UserService, UserServiceInterface

UserServiceDep = Annotated[UserServiceInterface, Depends(UserService)]
