python
# -*- coding: utf-8 -*-
from td_sqlalchemy import create_session, Column, Integer, Unicode, String

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(20))
    address = Column(String(100))

session = create_session(host="127.0.0.1:6041", database="mydatabase")

session.add(User(name="Alice", address="shanghai"))
session.commit()

for user in session.query(User).filter(User.name == "Alice").all():
    print(user.address)