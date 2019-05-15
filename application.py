#!/usr/bin/env python
# Created by Jacob Schaible

from flask import Flask, render_template, request, redirect, url_for
from flask import flash, jsonify, make_response
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, MenuItem, Order, OrderItem, Cart
from flask_login import login_user, logout_user, current_user
from flask_login import login_required, LoginManager
from werkzeug.urls import url_parse
from forms import LoginForm, RegistrationForm
import json


app = Flask(__name__)
login = LoginManager(app)
login.login_view = 'show_login'


def connect():
    """ Connect to database"""
    engine = create_engine('sqlite:///cantinadesantiago.db')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session


#################################
# User Authentication Functions #
#################################
@login.user_loader
def load_user(user_id):
    session = connect()
    user = session.query(User).filter_by(id=user_id).one_or_none()
    return user


def get_user_id(email):
    session = connect()
    user = session.query(User).filter_by(email=email).one_or_none()
    if user is None:
        return None
    else:
        return user.id


@app.route('/login', methods=['GET', 'POST'])
def show_login():
    session = connect()
    if current_user.is_authenticated:
        return redirect(url_for('show_menu'))
    form = LoginForm()
    if form.validate_on_submit():
        user = session.query(User).filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('show_login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('show_menu')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('show_menu'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    session = connect()
    if current_user.is_authenticated:
        return redirect(url_for('show_menu'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.username.data, email=form.email.data, admin=0)
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('show_login'))
    return render_template('register.html', title='Register', form=form)


###########################
# JSON Endpoint Functions #
###########################
@app.route('/menu/JSON')
def restaurant_menu_json():
    """ Returns list of menu items in JSON format"""
    session = connect()
    items = session.query(MenuItem).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/menu/<int:menu_id>/JSON')
def menu_item_json(menu_id):
    """ Returns one menu item in JSON format"""
    session = connect()
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(MenuItem=item.serialize)


######################
# Ordering Functions #
######################
@app.route('/cart/add/<int:menu_id>')
@login_required
def add_to_cart(menu_id):
    session = connect()
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    try:
        user_id = current_user.id
    except AttributeError:
        return "Error getting user ID"
    cart_item = Cart(user_id=user_id, menu_item_id=menu_id, quantity=1)
    session.add(cart_item)
    session.commit()
    flash("%s added to order!" % item.name)
    return redirect(url_for('show_menu'))


@app.route('/cart')
@login_required
def show_cart():
    session = connect()
    items = session.query(Cart).all()
    return render_template('cart.html', items=items)


#######################
# Menu CRUD Functions #
#######################
@app.route('/')
@app.route('/menu')
def show_menu():
    """ Display main menu page"""
    session = connect()
    items = session.query(MenuItem).all()
    try:
        if current_user.admin:
            return render_template('menu.html', items=items)
        else:
            return render_template('publicMenu.html', items=items)
    except AttributeError:
        return render_template('publicMenu.html', items=items)


@app.route('/menu/new', methods=['GET', 'POST'])
@login_required
def new_menu_item():
    """ Display page to create new menu item"""
    session = connect()
    if request.method == 'POST':
        newItem = MenuItem(name=request.form['name'],
                           course=request.form['course'],
                           description=request.form['description'],
                           price=request.form['price'])
        session.add(newItem)
        session.commit()
        flash("New menu item '%s' created!" % newItem.name)
        return redirect(url_for('show_menu'))
    else:
        return render_template('newMenuItem.html')


@app.route('/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_menu_item(menu_id):
    """ Display page to edit an existing menu item"""
    session = connect()
    item = session.query(MenuItem).filter_by(id=menu_id).one()
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
        return redirect(url_for('show_menu'))
    else:
        return render_template('editMenuItem.html', menu_id=menu_id, item=item)


@app.route('/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_menu_item(menu_id):
    """ Display page to delete an existing menu item"""
    session = connect()
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("Item '%s' deleted!" % item.name)
        return redirect(url_for('show_menu'))
    else:
        return render_template('deleteMenuItem.html', menu_id=menu_id,
                               item=item)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
