from flask import Flask, render_template, url_for, request, redirect, jsonify, make_response, flash, Response
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem
from flask import session as login_session
import random, string, json, httplib2, requests
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

# Connect to Database
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/catalog/JSON')
def getCatalog():

    output_json = []
    categories = session.query(Category).all()
    for category in categories:
        items = session.query(CategoryItem).filter_by(category_id=category.id)
        category_output = {}
        category_output["id"] = category.id
        category_output["name"] = category.name
        category_output["items"] = [i.serialize for i in items]
        output_json.append(category_output)
    return jsonify(Categories=output_json)


@app.route('/login')
def login():

    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state

    return render_template('login.html', STATE=state)

@app.route('/')
@app.route('/catalog', methods=['GET', 'POST'])
def baseDisplay():
    try:
        print 'lll'
        print login_session
        user = login_session['username']
    except KeyError:
        user = None
    if request.method == 'GET':
        STATE = ''.join(random.choice(string.ascii_uppercase +
            string.digits) for x in xrange(32))
        login_session['state'] = STATE
        categories = session.query(Category).all()
        categoryItems = session.query(CategoryItem).all()
        print 'rendering'
        return render_template('base.html', categories = categories, categoryItems = categoryItems, user=user, STATE=STATE)
    else:
        print ("Starting authentication")
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

        stored_credentials = login_session.get('credentials')
        stored_gplus_id = login_session.get('gplus_id')
        if stored_credentials is not None and gplus_id == stored_gplus_id:
            response = make_response(json.dumps('Current user is already connected.'),
                                     200)
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

        flash("you are now logged in as %s" % login_session['username'])
        print 'Redirecting'
        return redirect(url_for('baseDisplay'))


@app.route('/catalog/<int:catalog_id>')
@app.route('/catalog/<int:catalog_id>/items')

def displayCategory(catalog_id):
    categories = session.query(Category).all()
    category= session.query(Category).filter_by(id=catalog_id).first()
    categoryName= category.name
    categoryItems = session.query(CategoryItem).filter_by(category_id = catalog_id).all()
    categoryItemsCount = session.query(CategoryItem).filter_by(category_id = catalog_id).count()
    return render_template('displayCategory.html', categories = categories, categoryItems = categoryItems, categoryName = categoryName, categoryItemsCount = categoryItemsCount)

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>')
def displayCategoryItem(catalog_id, item_id):

    categoryItem = session.query(CategoryItem).filter_by(id = item_id).first()
    return render_template('displayItems.html', categoryItem = categoryItem)



@app.route('/catalog/items/new', methods=['GET', 'POST'])
def newCategoryItem():

    if 'username' not in login_session:
        return redirect(url_for('login'))
    categories = session.query(Category).all()
    if request.method == 'POST':
        if not request.form['name']:
                flash('Please add item name')
                return redirect(url_for('newCategoryItem'))

        if not request.form['description']:
            flash('Please add a description')
            return redirect(url_for('newCategoryItem'))

        newCategoryItem = CategoryItem(name = request.form['name'], description = request.form['description'], category_id = request.form['category'])
        session.add(newCategoryItem)
        session.commit()

        return redirect(url_for('baseDisplay'))
    else:

        categories = session.query(Category).all()

        return render_template('createItem.html', categories = categories)



@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/edit', methods=['GET', 'POST'])
def editCategoryItem(catalog_id, item_id):

    if 'username' not in login_session:
        return redirect(url_for('login'))
    categoryItem = session.query(CategoryItem).filter_by(id=item_id).first()
    categories = session.query(Category).all()
    if request.method == 'POST':
        if request.form['name']:
            categoryItem.name = request.form['name']
        if request.form['description']:
            categoryItem.description = request.form['description']
        if request.form['category_id']:
            categoryItem.category_id = request.form['category_id']
        session.add(categoryItem)
        session.commit()
        return redirect(url_for('baseDisplay'))
    else:
        return render_template('editItem.html', categories=categories, categoryItem=categoryItem)

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteCategoryItem(catalog_id, item_id):

    if 'username' not in login_session:
        return redirect(url_for('login'))


    categoryItem = session.query(CategoryItem).filter_by(id = item_id).first()

    if request.method == 'POST':
        session.delete(deletedItem)
        session.commit()
        return redirect(url_for('displayCategory', catalog_id = categoryItem.category_id))
    else:
        return render_template('deleteItem.html', categoryItem = categoryItem)


@app.route('/gdisconnect')
def gdisconnect():

    access_token = login_session.get('access_token')

    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('baseDisplay'))
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host = '0.0.0.0', port = 5000)