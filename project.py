from flask import (Flask, render_template, request,
                   redirect, jsonify, url_for, flash)
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# Load google api client info from client_secrets.json
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"

# Load item catalog from sqlite file
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    """ Displays login screen, shown when a user clicks 'Login'
        or attempts to access a secure part of the site.

        Returns:
            Html of the login screen.
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """ Callback for google login button.
        Logs the user into the site using the google auth apis.

        Returns:
            Html of google login success page, or failure information.
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
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
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

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
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
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

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """ Logs the user out of the site, uses google auth apis.
        Removes all locally stored session info.

        Returns:
            Html of categories index page, or logout error info.
    """
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % \
        login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        flash("Successfully logged out.")
        return redirect(url_for('categories'))
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/categories/<int:category_id>/items/JSON')
def categoryListJSON(category_id):
    """ RESTful api - used to query all items in a specific category

        Args:
            category_id: ID of the category to display.

        Returns:
            JSON representation of the requested category.
    """
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/categories/<int:category_id>/items/<int:item_id>/JSON')
def categoryItemJSON(category_id, item_id):
    """ RESTful api - used to query a specific item in a specific category

        Args:
            category_id: ID of the item's category.
            item_id: ID of the specific item to display.

        Returns:
            JSON representation of the requested item.
    """
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Items=item.serialize)


@app.route('/')
@app.route('/categories')
def categories():
    """ Shows all available categories.
        Home page routes to /categories

        Returns:
            Html of categories index page.
    """
    categories = session.query(Category).all()
    return render_template('categories.html', categories=categories,
                           logged_in=('username' in login_session))


@app.route('/categories/<int:category_id>/')
def categoryList(category_id):
    """ Shows all items for the selected category.

        Args:
            category_id: ID of the category to display.

        Returns:
            Html of categories index page with the given category displayed.
    """
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id)
    return render_template('items.html', categories=categories,
                           category=category, items=items,
                           logged_in=('username' in login_session))


@app.route('/categories/<int:category_id>/new', methods=['GET', 'POST'])
def newItem(category_id):
    """ Shows all items for the selected category.

        Args:
            category_id: ID of the category to display.

        Returns:
            Html of new item form to add an item to the given category.
    """
    if 'username' not in login_session:
        return redirect('/login')
    # If this is a post request, create a new item
    # using the supplied form fields.
    if request.method == 'POST':
        newItem = Item(name=request.form['name'], description=request.form[
                       'description'], category_id=category_id)
        session.add(newItem)
        session.commit()
        flash("new item created!")
        return redirect(url_for('categoryList', category_id=category_id))
    # If this is a get request, display the form used to create a new item.
    else:
        return render_template('newitem.html', category_id=category_id,
                               logged_in=('username' in login_session))


@app.route('/categories/<int:category_id>/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    """ Edits the selected item in the chosen category.

        Args:
            category_id: ID of the item's category.
            item_id: ID of the item to edit.

        Returns:
            Html of the edit item form to edit a specific item.
    """
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Item).filter_by(id=item_id).one()
    # If this is a post request, edit the item using the supplied form fields.
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash("item edited!")
        return redirect(url_for('categoryList', category_id=category_id))
    # If this is a get request, display the form used to edit
    # the selected item.
    else:
        return render_template('editItem.html', category_id=category_id,
                               item_id=item_id, item=editedItem,
                               logged_in=('username' in login_session))


@app.route('/category/<int:category_id>/<int:item_id>/delete/',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    """ Deletes the selected item in the chosen category.

        Args:
            category_id: ID of the item's category.
            item_id: ID of the item to delete.

        Returns:
            Html of the delete item confirmaion page.
    """
    if 'username' not in login_session:
        return redirect('/login')
    deletedItem = session.query(Item).filter_by(id=item_id).one()
    # If this is a post request, delete the item.
    if request.method == 'POST':
        session.delete(deletedItem)
        session.commit()
        flash("item deleted!")
        return redirect(url_for('categoryList', category_id=category_id))

    # If this is a get request, ask the user for confirmation
    # that the item should be deleted.
    else:
        return render_template('deleteItem.html', category_id=category_id,
                               item_id=item_id, item=deletedItem,
                               logged_in=('username' in login_session))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
