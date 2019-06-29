#!/usr/bin/env python
# Created by Jacob Schaible

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


class Address(Base):
    __tablename__ = 'address'
    id = Column(Integer, primary_key=True)
    street_1 = Column(String(250))
    street_2 = Column(String(250))
    city = Column(String(250))
    state = Column(String(250))
    zip_code = Column(String(5))

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'id': self.id,
            'street_1': self.street_1,
            'street_2': self.street_2,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code
        }


class User(UserMixin, Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    email = Column(String(250))
    password_hash = Column(String(250))
    address_id = Column(Integer, ForeignKey('address.id'))
    address = relationship(Address)
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
            'user_id': self.user_id,
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
            'user_id': self.user_id,
            'menu_item_id': self.menu_item_id,
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity,
        }


class OrderView(Base):
    __tablename__ = 'order_view'
    order_id = Column(Integer)
    menu_item_id = Column(Integer, primary_key=True)
    name = Column(String(80))
    price = Column(String(8))
    quantity = Column(Integer)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'order_id': self.order_id,
            'menu_item_id': self.menu_item_id,
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity,
        }


class TopItemView(Base):
    __tablename__ = 'top_item_view'
    menu_item_id = Column(Integer, primary_key=True)
    name = Column(String(80))
    description = Column(String(250))
    price = Column(String(8))
    quantity = Column(Integer)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'menu_item_id': self.menu_item_id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'quantity': self.quantity,
        }


class DayOfWeekView(Base):
    __tablename__ = 'day_of_week_view'
    day_of_week = Column(String(250), primary_key=True)
    quantity = Column(Integer)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'day_of_week': self.day_of_week,
            'quantity': self.quantity,
        }


class TimeOfDayView(Base):
    __tablename__ = 'time_of_day_view'
    time_of_day = Column(String(2), primary_key=True)
    quantity = Column(Integer)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'time_of_day': self.time_of_day,
            'quantity': self.quantity,
        }


class ZipCodeView(Base):
    __tablename__ = 'zip_code_view'
    zip_code = Column(String(5), primary_key=True)
    quantity = Column(Integer)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'zip_code': self.zip_code,
            'quantity': self.quantity
        }


engine = create_engine('sqlite:///cantinadesantiago.db')
Base.metadata.create_all(engine)
