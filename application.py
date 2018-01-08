from flask import Flask, render_template, \
    request, redirect, jsonify, url_for, flash, make_response

# Session works as a dictionary storing
# information for the longevity of a user's session with the server
from flask import session as login_session

# Database information
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import Base, User, Sport, SportItem

import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///sportcatalog.db')
Base.metadata.bind = engine

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = 'Sport Catalog App'

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Route to the home page
@app.route('/')
@app.route('/sport')
def home():
    return render_template('index.html')


@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase
                                  + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=login_session['state'])


# login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# Creating a new User
def create_user(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        image=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(
        email=login_session['email']).one()
    return user.id


# Getting User info
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Getting User info
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Adding Facebook login
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?' \
          'grant_type=fb_exchange_token&client_id=%s&client_secret=%s' \
          '&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    print 'result is %s' % result

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    print 'result is %s' % result

    data = json.loads(result)
    print 'data is %s' % result

    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s' \
          '&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    print data
    print 'picture gotten'

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id
    print 'going fine'

    output = ''
    output += '<h6>Welcome, '
    output += login_session['username']
    output += '!</h6>'

    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px; height: 300px;' \
              'border-radius: 150px;-webkit-border-radius: ' \
              '150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


# Disconnecting a facebook User
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


# Adding google plus login
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(
            json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(
            json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id
    print 'going fine'

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: ' \
              '150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# Disconnecting a google User
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    categories = session.query(Sport).all()
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('sport_category', categories=categories))
    else:
        flash("You have not been logged in")
        return redirect(url_for('sport_category', categories=categories))


# Route for the category page
@app.route('/sport/catalog')
@login_required
def sport_category():
    categories = session.query(Sport).all()
    items = session.query(SportItem).\
        order_by(desc(SportItem.id)).limit(6)
    if 'user_id' not in login_session:
        return render_template(
            'publichomepage.html', categories=categories, items=items)
    else:
        return render_template(
            'homepage.html', categories=categories, items=items)


# Route for creating a new Category
@app.route('/sport/catalog/new', methods=['GET', 'POST'])
@login_required
def new_category():
    if request.method == 'POST':
        newCategory = Sport(
            name=request.form['name'], user_id=login_session['user_id'])
        session.commit()
        flash('New Category %s successfully created' % newCategory.name)
        return redirect(url_for(sport_category))
    else:
        return render_template('newCategory.html')


# Route for editing Category
@app.route('/sport/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_catalog(category_id):
    editedCategory = session.query(Sport).filter_by(id=category_id).one()
    if editedCategory.user_id != login_session['user_id']:
        return "<script> function myFunction() {" \
               "alert('You are not authorized to edit this item. " \
               "Please create your own item before you proceed.');" \
               "}" \
               "</script>" \
               "<body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash(' %s has successfully been edited' % editedCategory.name)
            return redirect(sport_category)
    else:
        return render_template('editcatalog.html', category=editedCategory)


# Route for deleting Category
@app.route('/sport/<int:category_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_category(category_id):
    deleteCategory = session.query(Sport).filter_by(id=category_id).one()
    if deleteCategory.user_id != login_session['user_id']:
        return "<script> function myFunction() {" \
               "alert('You are not authorized to edit this item. " \
               "Please create your own item before you proceed.');" \
               "}" \
               "</script>" \
               "<body onload='myFunction()'>"
    if request.method == "POST":
        session.delete(deleteCategory)
        session.commit()
        flash('%s successfully deleted' % deleteCategory.name)
        return redirect(sport_category)
    else:
        return render_template('deletecategory.html', category=deleteCategory)


# Route to display the items in each category
@app.route('/sport/<int:category_id>/item')
@login_required
def category_item(category_id):
    categories = session.query(Sport).all()
    category_heading = session.query(Sport).filter_by(id=category_id).one()
    item = session.query(SportItem).filter_by(sport_id=category_id).all()
    total = len(item)
    if 'username' not in login_session:
        return render_template('publicitem.html', category=category_heading, categories=categories, item=item,
                               total=total)
    else:
        return render_template('items.html', category=category_heading, categories=categories, item=item, total=total)


# Route leading to the description of each item
@app.route('/sport/<int:category_id>/<int:item_id>/description')
@login_required
def itemDescription(category_id, item_id):
    category = session.query(Sport).filter_by(id=category_id).one()
    item = session.query(SportItem).filter_by(id=item_id).one()
    if 'username' not in login_session:
        return render_template('publicdescription.html', category=category, item=item)
    else:
        return render_template('description.html', category=category, item=item)


# Route for adding a new item to a category
@app.route('/sport/<int:category_id>/item/new', methods=['GET', 'POST'])
@login_required
def newitem(category_id):
    categories = session.query(Sport).all()
    category_heading = session.query(Sport).filter_by(id=category_id).one()
    if login_session['user_id'] != category_heading.user_id:
        return "<script> function myFunction() {" \
               "alert('You are not authorized to create a new item. " \
               "Please create your own item before you proceed.');" \
               "}" \
               "</script>" \
               "<body onload='myFunction()'>"
    if request.method == 'POST':
        newItem = SportItem(name=request.form['name'], description=request.form['description'],
                            sport_id=category_id, user_id=category_heading.user_id)
        session.add(newItem)
        session.commit()
        flash('%s Successfully added to %s ' % (newItem.name, category_heading.name))
        return redirect(url_for('sport_category', categories=categories))
    else:
        return render_template('additems.html', categories=categories, category=category_heading)


# Route for editing an item in a category
@app.route('/sport/<int:category_id>/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(category_id, item_id):
    categories = session.query(Sport).all()
    category = session.query(Sport).filter_by(id=category_id).one()
    item = session.query(SportItem).filter_by(id=item_id).one()
    if login_session['user_id'] != category.user_id:
        return "<script> function myFunction() {" \
               "alert('You are not authorized to edit this item. " \
               "Please create your own item before you proceed.');" \
               "}" \
               "</script>" \
               "<body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        session.add(item)
        session.commit()
        flash('%s Successfully Edited ' % item.name)
        return redirect(url_for('sport_category', categories=categories))
    else:
        return render_template('edititem.html', item=item, categories=categories, category=category)


# Route for delete an item
@app.route('/sport/<int:category_id>/<int:item_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_item(category_id, item_id):
    categories = session.query(Sport).all()
    category = session.query(Sport).filter_by(id=category_id).one()
    item = session.query(SportItem).filter_by(id=item_id).one()
    if login_session['user_id'] != category.user_id:
        return "<script> function myFunction() {" \
               "alert('You are not authorized to delete this item. " \
               "Please create your own item before you proceed.');" \
               "}" \
               "</script>" \
               "<body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash('%s Successfully Deleted ' % item.name)
        return redirect(url_for('sport_category', categories=categories))
    else:
        return render_template('delete.html', category=category, item=item)


# This is for JSON API endpoint for list of sport categories
@app.route('/sport/category/JSON')
def categoryJSON():
    categories = session.query(Sport).all()
    return jsonify(Sport_categories=[category.serialize for category in categories])


# This is for JSON API endpoint for list of items in each category
@app.route('/sport/<int:category_id>/items/JSON')
def itemsJSON(category_id):
    items = session.query(SportItem).filter_by(sport_id=category_id)
    return jsonify(Item_sport_category=[item.serialize for item in items])


# This is for JSON API endpoint for description of items in each category
@app.route('/sport/<int:category_id>/<int:item_id>/JSON')
def description(category_id, item_id):
    category = session.query(Sport).filter_by(id=category_id).one()
    item = session.query(SportItem).filter_by(id=item_id).one()
    return jsonify(Item_description=[item.serialize])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
