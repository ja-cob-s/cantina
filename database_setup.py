#!/usr/bin/env python3

import sys
import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
from sqlalchemy.sql import func

Base = declarative_base()


class User(UserMixin, Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    email = Column(String(250))
    password_hash = Column(String(250))
    address = Column(String(250))
    admin = Column(Integer)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class MenuItem(Base):
    __tablename__ = 'menu_item'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    course = Column(String(250), nullable=False)
    description = Column(String(250))
    price = Column(String(8), nullable=False)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'id': self.id,
            'name': self.name,
            'course': self.course,
            'description': self.description,
            'price': self.price,
        }


class Order(Base):
    __tablename__ = 'order'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    order_time = Column(DateTime(timezone=True), server_default=func.now())
    delivery_time = Column(DateTime(timezone=True))

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_time': self.order_time,
            'delivery_time': self.delivery_time,
        }


class OrderItem(Base):
    __tablename__ = 'order_item'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('order.id'))
    order = relationship(Order, backref=backref(
                            'order_item', cascade='all, delete'))
    menu_item_id = Column(Integer, ForeignKey('menu_item.id'))
    menu_item = relationship(MenuItem)
    quantity = Column(Integer, nullable=False)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'id': self.id,
            'order_id': self.order_id,
            'menu_item_id': self.menu_item_id,
            'quantity': self.quantity,
        }


class Cart(Base):
    __tablename__ = 'cart'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    menu_item_id = Column(Integer, ForeignKey('menu_item.id'))
    menu_item = relationship(MenuItem)
    quantity = Column(Integer, nullable=False)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'id': self.id,
            'user_id': self.order_id,
            'menu_item_id': self.menu_item_id,
            'quantity': self.quantity,
        }


class CartView(Base):
    __tablename__ = 'cart_view'
    user_id = Column(Integer)
    menu_item_id = Column(Integer, primary_key=True)
    name = Column(String(80))
    price = Column(String(8))
    quantity = Column(Integer)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'user_id': self.order_id,
            'menu_item_id': self.menu_item_id,
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity,
        }


engine = create_engine('sqlite:///cantinadesantiago.db')
Base.metadata.create_all(engine)
