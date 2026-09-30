from dependencies import UserRepositoryDep
from utils.hash import verify_password


class LoginService():
    def __init__(self, repo: UserRepositoryDep):
        self.repo = repo
    def login(self, email: str, pwd: str) -> bool:
        user = self.repo.get_by_email(email)
        if not user:
            return False
        return verify_password(pwd, user.password)
        