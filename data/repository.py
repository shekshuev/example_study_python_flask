from abc import ABCMeta, abstractmethod
from datetime import datetime
from data.models.account import Account
from data.models.log import Log
from data.dto.account_dto import AccountDTO
from typing import List
import psycopg
from psycopg.rows import dict_row
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()


class RepositoryException(Exception):
    pass


class Repository(metaclass=ABCMeta):

    @abstractmethod
    def get_all_accounts(self, user_id: int = None) -> List[Account]:
        pass

    @abstractmethod
    def get_account_by_id(self, id: int, user_id: int = None) -> Account:
        pass

    @abstractmethod
    def get_account_by_username_and_password(self, username: str, password: str, user_id: int = None) -> Account:
        pass

    @abstractmethod
    def create_account(self, account_dto: AccountDTO, user_id: int = None):
        pass

    @abstractmethod
    def update_account(self, id: int, account_dto: AccountDTO, user_id: int = None):
        pass

    @abstractmethod
    def delete_account_by_id(self, id: int, user_id: int = None):
        pass

    def get_logs(self) -> List[Log]:
        pass


class PostgreSQLRepository(Repository):

    def __init__(self) -> None:
        self.__connection = psycopg.connect(f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}",row_factory=dict_row)
        self.__cursor = self.__connection.cursor()
        try:
            self.__cursor.execute("""
                                  create table if not exists accounts (
                                  id serial primary key, 
                                  username text not null unique, 
                                  firstname text, 
                                  lastname text, 
                                  middlename text not null, 
                                  password_hash text not null, 
                                  role text not null)
                                  """)
            self.__connection.commit()
            self.__cursor.execute("""
                                  create table if not exists logs (
                                  id serial primary key, 
                                  created_at timestamp not null, 
                                  type text not null, 
                                  user_id int, 
                                  event text not null, 
                                  reason text, 
                                  foreign key (user_id) references accounts(id))
                                  """)
            self.__connection.commit()
        except Exception as e:
            self.__connection.rollback()
            print(e)
        try:
            self.__cursor.execute("""
                                  insert into accounts 
                                  (username, firstname, lastname, middlename, password_hash, role) 
                                  values ('admin', 'John', 'Doe', 'J.', %s, 'admin')
                                  """, (generate_password_hash('admin'),))
            self.__connection.commit()
        except Exception as e:
            self.__connection.rollback()
            print(e)

    def get_all_accounts(self, user_id: int = None) -> List[Account]:
        try:
            self.__cursor.execute("select * from accounts")
            accounts = self.__cursor.fetchall()
            self.__create_log("INFO", user_id, "GET_ACCOUNTS")
            return [Account(id=account["id"],
                            username=account["username"],
                            firstname=account["firstname"] if "firstname" in account.keys() else "",
                            lastname=account["lastname"] if "lastname" in account.keys() else "", 
                            middlename=account["middlename"] if "middlename" in account.keys() else "", 
                            role=account["role"]) for account in accounts]
        except Exception as e:
            self.__create_log("ERROR", user_id, "GET_ACCOUNTS", str(e))
            raise RepositoryException(str(e))

    def get_account_by_username_and_password(self, username: str, password: str, user_id: int = None) -> Account:
        try:
            self.__cursor.execute("""select * from accounts where username = %s""", (username,))
            account = self.__cursor.fetchone()
            if account:
                if check_password_hash(account["password_hash"], password):
                    self.__create_log("INFO", user_id, "GET_ACCOUNT")
                    return Account(id=account["id"],
                                   username=account["username"],
                                   firstname=account["firstname"] if "firstname" in account.keys() else "",
                                   lastname=account["lastname"] if "lastname" in account.keys() else "",
                                   middlename=account["middlename"] if "middlename" in account.keys() else "",
                                   role=account["role"])
                else:
                    raise ValueError("Неверный пароль")
            else:
                raise ValueError("Учетная запись не найдена")
        except Exception as e:
            self.__create_log("ERROR", user_id, "GET_ACCOUNT", str(e))
            raise RepositoryException(str(e))

    def get_account_by_id(self, id: int, user_id: int = None) -> Account:
        try:
            self.__cursor.execute("""select * from accounts WHERE id = %s """, (id, ))
            account = self.__cursor.fetchone()
            self.__create_log("INFO", user_id, "GET_ACCOUNT")
            return Account(id=account["id"],
                           username=account["username"],
                           firstname=account["firstname"] if "firstname" in account.keys() else "",
                           lastname=account["lastname"] if "lastname" in account.keys() else "",
                           middlename=account["middlename"] if "middlename" in account.keys() else "",
                           role=account["role"])
        except Exception as e:
            self.__create_log("ERROR", user_id, "GET_ACCOUNT", str(e))
            raise RepositoryException(str(e))

    def create_account(self, account_dto: AccountDTO, user_id: int = None):
        try:
            self.__cursor.execute("""insert into accounts 
                                  (username, firstname, lastname, middlename, password_hash, role) 
                                  values (%s, %s, %s, %s, %s, %s)
                                  """, (account_dto.username, 
                                        account_dto.firstname, 
                                        account_dto.lastname, 
                                        account_dto.middlename, 
                                        generate_password_hash(account_dto.password), 
                                        account_dto.role))
            self.__connection.commit()
            self.__create_log("INFO", user_id, "CREATE_ACCOUNT")
        except Exception as e:
            self.__create_log("ERROR", user_id, "CREATE_ACCOUNT", str(e))
            raise RepositoryException(str(e))

    def update_account(self, id: int, account_dto: AccountDTO, user_id: int = None):
        try:
            self.__cursor.execute("""update accounts set 
                                  username=%s, firstname=%s, lastname=%s, 
                                  middlename=%s,password_hash=%s, role=%s where id=%s
                                  """, (
                                      account_dto.username,
                                      account_dto.firstname,
                                      account_dto.lastname,
                                      account_dto.middlename,
                                      generate_password_hash(account_dto.password),
                                      account_dto.role,
                                      id))
            self.__connection.commit()
            self.__create_log("INFO", user_id, "UPDATE_ACCOUNT")
        except Exception as e:
            self.__create_log("ERROR", user_id, "UPDATE_ACCOUNT", str(e))
            raise RepositoryException(str(e))

    def delete_account_by_id(self, id: int, user_id: int = None):
        try:
            self.__cursor.execute("""delete from accounts where id=%s""", (id,))
            self.__connection.commit()
            self.__create_log("INFO", user_id, "DELETE_ACCOUNT")
        except Exception as e:
            self.__create_log("ERROR", user_id, "DELETE_ACCOUNT", str(e))
            raise RepositoryException(str(e))

    def get_logs(self) -> List[Log]:
        self.__cursor.execute("select * from logs")
        logs = self.__cursor.fetchall()
        return [Log(id=log["id"],
                    date=log["created_at"].date(),
                    time=log["created_at"].time(),
                    type=log["type"],
                    user_id=log["user_id"] if "user_id" in log.keys() else None,
                    event=log["event"],
                    reason=log["reason"] if "reason" in log.keys() else "") for log in logs]

    def __create_log(self, event_type: str, user_id: int, event: str, reason: str = None):
        self.__cursor.execute("""insert into logs 
                              (created_at, type, user_id, event, reason) 
                              values (now(), %s, %s, %s, %s)
                              """, (event_type, user_id, event, reason))
        self.__connection.commit()


def get_repository() -> Repository:
    return PostgreSQLRepository()
