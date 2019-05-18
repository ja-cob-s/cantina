#!/usr/bin/env python
# Created by Jacob Schaible

from flask import Flask, render_template, request, redirect, url_for
from flask import flash, jsonify, make_response
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, MenuItem, Order, OrderItem
from database_setup import Cart, CartView, TopItemView
from flask_login import login_user, logout_user, current_user
from flask_login import login_required, LoginManager
from werkzeug.urls import url_parse
from forms import LoginForm, RegistrationForm
import json, urllib2, datetime

app = Flask(__name__)
login = LoginManager(app)
login.login_view = 'show_login'


DELIVERY_FEE = 2.99
RESTAURANT_ADDRESS = '13020 Livingston Rd, Naples, FL 34105'
APP_KEY = open('gmaps_api_key.txt', 'r').read()
MAX_DELIVERY_DISTANCE = 32187  # Distance in meters, roughly equals 20 miles


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
    """ Get user matching given user ID"""
    session = connect()
    user = session.query(User).filter_by(id=user_id).one_or_none()
    return user


@app.route('/login', methods=['GET', 'POST'])
def show_login():
    """ Display the login page and validate credentials"""
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
    """ Logout the current user"""
    logout_user()
    return redirect(url_for('show_menu'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """ Sign up a new user"""
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
    """ Add a menu item to the user's cart
        If item already exists in cart, increment the quantity
    """
    session = connect()
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    try:
        user_id = current_user.id
    except AttributeError:
        return "Error getting user ID"
    cart_item = Cart(user_id=user_id, menu_item_id=menu_id, quantity=1)
    existing_item = session.query(Cart).filter_by(
        user_id=user_id, menu_item_id=menu_id).one_or_none()
    if existing_item:
        existing_item.quantity += 1
        cart_item = existing_item
    session.add(cart_item)
    session.commit()
    flash("%s added to order!" % item.name)
    return redirect(url_for('show_menu'))


@app.route('/cart/update/<int:menu_id>', methods=['GET', 'POST'])
@login_required
def update_cart(menu_id):
    """ Update the quantity of a menu item in the user's cart"""
    session = connect()
    try:
        user_id = current_user.id
    except AttributeError:
        return "Error getting user ID"
    item = session.query(Cart).filter_by(
        user_id=user_id, menu_item_id=menu_id).one()
    if request.method == 'POST':
        if request.form['quantity']:
            item.quantity = request.form['quantity']
            flash("Quantity updated")
        session.add(item)
        session.commit()
    return redirect(url_for('show_cart'))


@app.route('/cart/remove/<int:menu_id>')
@login_required
def remove_from_cart(menu_id):
    """ Remove a menu item from the user's cart"""
    session = connect()
    try:
        user_id = current_user.id
    except AttributeError:
        return "Error getting user ID"
    item = session.query(Cart).filter_by(
        user_id=user_id, menu_item_id=menu_id).one()
    menu_item = session.query(MenuItem).filter_by(id=menu_id).one()
    session.delete(item)
    session.commit()
    flash("%s removed from order!" % menu_item.name)
    return redirect(url_for('show_cart'))


@app.route('/cart')
@login_required
def show_cart():
    """ Display the contents of the user's cart"""
    session = connect()
    try:
        user_id = current_user.id
    except AttributeError:
        return "Error getting user ID"
    items = session.query(CartView).filter_by(user_id=user_id).all()
    subtotal = 0.0
    for item in items:
        subtotal += float(item.price) * item.quantity
    if subtotal > 0:
        fee = DELIVERY_FEE
    else:
        fee = 0
    tax = (subtotal + fee) * 0.07
    total = subtotal + fee + tax
    subtotal = "{0:.2f}".format(subtotal)
    fee = "{0:.2f}".format(fee)
    tax = "{0:.2f}".format(tax)
    total = "{0:.2f}".format(total)
    delivery_time = str(get_delivery_time()/60) + ' minutes'
    return render_template('cart.html', items=items, subtotal=subtotal,
                           fee=fee, tax=tax, total=total, user=current_user,
                           delivery_time=delivery_time)


@app.route('/cart/update_address', methods=['GET', 'POST'])
@login_required
def update_address():
    """ Update the user's address"""
    session = connect()
    user = load_user(current_user.id)
    if request.method == 'POST':
        if request.form['address']:
            address = request.form['address']
            if validate_address(address) is False:
                flash("Address is invalid or outside delivery radius!")
                return redirect(url_for('show_cart'))
            user.address = address
            user = session.merge(user)
            flash("Address saved!")
            session.commit()
    return redirect(url_for('show_cart'))


def validate_address(address):
    """ Validates the address string
        Returns true if valid, false if not
    """
    # User has no address saved
    if address is None:
        return False
    # User is outside delivery radius
    if get_travel_distance(address) > MAX_DELIVERY_DISTANCE:
        return False
    # If none of the above cases returned false, the address is okay
    return True


@app.route('/cart/order_placed')
@login_required
def place_order():
    """ Place order for delivery for the items currently in the user's cart"""
    session = connect()
    try:
        user_id = current_user.id
    except AttributeError:
        return "Error getting user ID"
    # Query for cart contents
    items = session.query(Cart).filter_by(user_id=user_id).all()
    # Redirect user if no items in order
    if not items:
        flash("No items in order!")
        return redirect(url_for('show_cart'))
    # Make sure customer's address is valid
    destination = current_user.address
    if validate_address(destination) is False:
        flash("Address is invalid or outside delivery radius!")
        return redirect(url_for('show_cart'))
    # Create new entry in order table
    order_time = datetime.datetime.now()
    delivery_time = order_time + datetime.timedelta(0,get_delivery_time())
    new_order = Order(user_id=user_id, order_time=order_time,
                      delivery_time=delivery_time)
    session.add(new_order)
    order = session.query(Order).filter_by(order_time=order_time).one()
    # Add each item to order_item table and remove from cart
    for i in items:
        order_item = OrderItem(order_id=order.id, menu_item_id=i.menu_item_id,
                               quantity=i.quantity)
        session.add(order_item)
        session.delete(i)
    session.commit()
    # Convert delivery time to EST and format for display
    delivery_time = delivery_time - datetime.timedelta(hours=4)
    delivery_time = delivery_time.strftime('%I:%M %p')
    # Form URL for delivery map
    origin = RESTAURANT_ADDRESS.replace(' ', '+')
    destination = destination.replace(' ', '+')
    destination = destination.replace('\r\n', '+')
    destination = destination.replace('\r', '+')
    destination = destination.replace('\n', '+')
    map_url = 'https://www.google.com/maps/embed/v1/directions?origin='
    map_url += origin
    map_url += '&destination='
    map_url += destination
    map_url += '&key='
    map_url += APP_KEY
    return render_template('orderComplete.html', delivery_time=delivery_time,
                           map_url=map_url)


######################
# Delivery Functions #
######################
def get_travel_data(destination):
    """ Returns JSON travel data"""
    origin = RESTAURANT_ADDRESS.replace(' ', '+')
    destination = destination.replace(' ', '+')
    destination = destination.replace('\r\n', '+')
    destination = destination.replace('\r', '+')
    destination = destination.replace('\n', '+')
    url = 'https://maps.googleapis.com/maps/api/directions/json?origin='
    url += origin
    url += '&destination='
    url += destination
    url += '&mode=driving&key='
    url += APP_KEY
    travel_data = json.load(urllib2.urlopen(url))
    return travel_data

def get_travel_time(destination):
    """ Returns travel time in seconds between restaurant
        and destination for delivery
    """
    travel_data = get_travel_data(destination)
    return travel_data['routes'][0]['legs'][0]['duration']['value']


def get_travel_distance(destination):
    """ Returns travel distance in meters between restaurant
        and destination for delivery
    """
    travel_data = get_travel_data(destination)
    return travel_data['routes'][0]['legs'][0]['distance']['value']


def get_prep_time():
    #TODO
    return 1200


def get_delivery_time():
    """ The delivery time is the combination of 
        the prep time and the travel time
    """
    try:
        delivery_time = get_travel_time(current_user.address)
        delivery_time += get_prep_time()
        return delivery_time
    except AttributeError:
        return "Error getting user address"


#######################
# Menu CRUD Functions #
#######################
@app.route('/')
@app.route('/menu')
def show_menu():
    """ Display main menu page"""
    session = connect()
    items = session.query(MenuItem).all()
    top_items = session.query(TopItemView).all()
    # Customers and those not logged in should see publicMenu
    # while admins should see adminMenu
    try:
        if current_user.admin:
            return render_template('adminMenu.html', items=items,
                                   top_items=top_items)
        else:
            return render_template('publicMenu.html', items=items,
                                   top_items=top_items)
    except AttributeError:
        return render_template('publicMenu.html', items=items,
                               top_items=top_items)


@app.route('/admin/new', methods=['GET', 'POST'])
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


@app.route('/admin/edit/<int:menu_id>', methods=['GET', 'POST'])
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


@app.route('/admin/delete/<int:menu_id>', methods=['GET', 'POST'])
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


######################################
# Administrative Dashboard Functions #
######################################
@app.route('/admin/dashboard')
@login_required
def show_dashboard():
    """ Display the administrative dashboard which provides analytic
        data such as most popular items, busiest times, and top locations
        of customers
    """
    # Must be admin to view this page
    try:
        if not current_user.admin:
            flash("You don't have permission to view this page.")
            return redirect(url_for('show_menu'))
    except AttributeError:
        flash("Error determining user privledges.")
        return redirect(url_for('show_menu'))
    session = connect()
    top_items = session.query(TopItemView).all()
    return render_template('dashboard.html', top_items=top_items)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
