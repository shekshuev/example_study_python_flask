from data.models.account import Account


class AccountLoginState:

    def __init__(self, account: Account) -> None:
        self.__id = account.id
        self.__username = account.username
        self.__role = account.role

    @property
    def id(self):
        return self.__id

    @property
    def username(self):
        return self.__username

    @property
    def role(self):
        return self.__role

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.__id)
