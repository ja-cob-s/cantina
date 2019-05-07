#!/usr/bin/env python
# Created by Jacob Schaible

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, MenuItem, Order, OrderItem


app = Flask(__name__)


def connect():
    """ Connect to database"""
    engine = create_engine('sqlite:///cantinadesantiago.db')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind = engine)
    session = DBSession()
    return session


#########################
# User Helper Functions #
#########################
def createUser(login_session):
    """ Creates a new user in the database"""
    session = connect()
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """ Returns user object or None if user not found"""
    session = connect()
    user = session.query(User).filter_by(id=user_id).one_or_none()
    return user


def getUserID(email):
    """ Returns user.id of the user or None if user not found"""
    session = connect()
    user = session.query(User).filter_by(email=email).one_or_none()
    if user is None:
        return None
    else:
        return user.id


#########################
# JSON Helper Functions #
#########################
@app.route('/menu/JSON')
def restaurantMenuJSON():
    """ Returns list of menu items in JSON format"""
    session = connect()
    items = session.query(MenuItem).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/menu/<int:menu_id>/JSON')
def menuItemJSON(menu_id):
    """ Returns one menu item in JSON format"""
    session = connect()
    item = session.query(MenuItem).filter_by(id = menu_id).one()
    return jsonify(MenuItem=item.serialize)


#########################
# CRUD Helper Functions #
#########################
@app.route('/')
@app.route('/menu')
def showMenu():
    """ Display main menu page"""
    session = connect()
    items = session.query(MenuItem).all()
    return render_template('menu.html', items=items)


@app.route('/menu/new', methods=['GET', 'POST'])
def newMenuItem():
    """ Display page to create new menu item"""
    session = connect()
    if request.method == 'POST':
        newItem = MenuItem(name = request.form['name'], course = request.form['course'],
            description = request.form['description'], price = request.form['price'])
        session.add(newItem)
        session.commit()
        flash("New menu item '%s' created!" % newItem.name)
        return redirect(url_for('showMenu'))
    else:
        return render_template('newMenuItem.html')


@app.route('/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
def editMenuItem(menu_id):
    """ Display page to edit an existing menu item"""
    session = connect()
    item = session.query(MenuItem).filter_by(id = menu_id).one()
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
            flash("Item renamed to '%s'!" % item.name)
        if request.form['price']:
            item.price = request.form['price']
            flash("Item '%s' price changed to %s!" % (item.name, item.price))
        if request.form['description']:
            item.description = request.form['description']
            flash("Item '%s' description changed!" % item.name)
        if request.form['course'] != item.course:
            item.course = request.form['course']
            flash("Item '%s' course changed to %s!" % (item.name, item.course))
        session.add(item)
        session.commit()
        return redirect(url_for('showMenu'))
    else:
        return render_template('editMenuItem.html', menu_id = menu_id, item=item)


@app.route('/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(menu_id):
    """ Display page to delete an existing menu item"""
    session = connect()
    item = session.query(MenuItem).filter_by(id = menu_id).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("Item '%s' deleted!" % item.name) 
        return redirect(url_for('showMenu'))
    else:
        return render_template('deleteMenuItem.html', menu_id = menu_id, item=item)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)