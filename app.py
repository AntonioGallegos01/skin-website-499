#import mysql.connector
#from prettytable import PrettyTable
#from prettytable import from_db_cursor
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, url_for , redirect, jsonify, request,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# this just keeps tabs on user making request
app.secret_key = 'super_secret_key'
# this creates that connection to mysql CI KEYS 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://antoniog_skin:Jan122001%21@antoniogallegos063.cikeys.com/antoniog_skin'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# DEFINES TABLES HERE
class SKIN_TYPE(db.Model):
    __tablename__ = 'SKIN_TYPE'
    skin_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    skin_type_name = db.Column(db.String(24), nullable=False)
    skin_type_description = db.Column(db.String(124))
    def __repr__(self):
        return f"<SKIN_TYPE {self.skin_type_name}>"
    
class APP_USER(db.Model):
    __tablename__ = 'APP_USER'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(80), unique=True, nullable=False)
    user_fname = db.Column(db.String(64), nullable=True)
    user_lname = db.Column(db.String(64), nullable=True)
    user_passwd = db.Column(db.String(64), nullable=False)
    user_skin_type = db.Column(db.Integer, db.ForeignKey('SKIN_TYPE.skin_type_id'), nullable=True)
    user_loginTime = db.Column(db.DateTime, nullable=True)
    def __repr__(self):
        return f"<APP_USER {self.user_email}>"
    
class PRODUCT(db.Model):
    __tablename__ = 'PRODUCT'

    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    product_name = db.Column(db.String(80), nullable=False)

    product_brand_id = db.Column(db.Integer,db.ForeignKey('BRAND.brand_id'),nullable=True)

    product_category = db.Column(db.Integer,db.ForeignKey('PRODUCT_CATEGORY.category_id'),nullable=True)

    product_skin_type = db.Column(db.Integer,db.ForeignKey('SKIN_TYPE.skin_type_id'),nullable=True)

    product_upc = db.Column(db.String(20), unique=True, nullable=True)

    product_release = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f"<PRODUCT {self.product_name}>"
    
class USER_PRODUCT(db.Model):
    __tablename__ = 'USER_PRODUCT'

    user_id = db.Column(db.Integer, db.ForeignKey('APP_USER.user_id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('PRODUCT.product_id'), primary_key=True)

    breakout = db.Column(db.Boolean, default=False)
    drying = db.Column(db.Boolean, default=False)
    oily = db.Column(db.Boolean, default=False)
    hydrating = db.Column(db.Boolean, default=False)
    heavy = db.Column(db.Boolean, default=False)
    recommend = db.Column(db.Boolean, default=False)

# when / used logs the log in to the site will redirect to the tables
@app.route('/')
def home():
    # Redirect to /tables
    return render_template('home.html')
# the route to add users
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('user_email')
        password = request.form.get('user_passwd')
        # this checks the email and selects the first email on list
        user = APP_USER.query.filter_by(user_email=email).first()

        if user and check_password_hash(user.user_passwd, password):
            #store theu user info in session 
            session['user_id'] = user.user_id
            session['user_email'] = user.user_email

            return redirect(url_for('dashboard'))
        else:
            return "Invalid email or password"
    return render_template('login.html')

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        # Use form data if JSON is not sent
        data = request.form

        # Gets the user info from the format html file
        user_email = data.get('user_email')
        user_fname = data.get('user_fname')
        user_lname = data.get('user_lname')
        user_passwd = data.get('user_passwd')
        user_skin_type = data.get('user_skin_type')
        user_loginTime = datetime.now()
        # Hashes the password input for safety
        hashed_password = generate_password_hash(user_passwd)

        # Assigns the variables to the correct format
        new_user = APP_USER(
            user_email=user_email,
            user_fname=user_fname,
            user_lname=user_lname,
            user_passwd=hashed_password,
            user_skin_type=user_skin_type,
            user_loginTime=user_loginTime
        )
        # here added it the sql 
        db.session.add(new_user)
        # Here basically commits it
        db.session.commit()

        return redirect(url_for('list_users'))

    # If GET, just show the HTML form
    skin_types = SKIN_TYPE.query.all()
    return render_template('add_user.html', skin_types=skin_types)

@app.route('/users')
def list_users():
    # Join APP_USER with SKIN_TYPE to get the skin type name
    users = db.session.query(APP_USER, SKIN_TYPE).join(
        SKIN_TYPE, APP_USER.user_skin_type == SKIN_TYPE.skin_type_id, isouter=True
    ).all()

    # Transform the data into a list of dicts for the template
    user_list = []
    for user, skin in users:
        user_list.append({
            'user_id': user.user_id,
            'user_email': user.user_email,
            'user_fname': user.user_fname,
            'user_lname': user.user_lname,
            'user_skin_type_name': skin.skin_type_name if skin else "None",
            'user_loginTime': user.user_loginTime
        })

    return render_template('users.html', users=user_list)

@app.route('/my_reviews')
def my_reviews():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    query = """
        SELECT *
        FROM user_product_review_view
        WHERE user_id = :user_id
    """

    reviews = db.session.execute(
        db.text(query),
        {"user_id": user_id}
    ).fetchall()

    return render_template(
        'my_reviews.html',
        reviews=reviews
    )

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add_review', methods=['GET', 'POST'])
def add_review():

    # Must be logged in first
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # POST = user submits review form
    if request.method == 'POST':

        user_id = session['user_id']
        product_id = request.form.get('product_id')

        breakout = request.form.get('breakout') == 'yes'
        drying = request.form.get('drying') == 'yes'
        oily = request.form.get('oily') == 'yes'
        hydrating = request.form.get('hydrating') == 'yes'
        heavy = request.form.get('heavy') == 'yes'
        recommend = request.form.get('recommend') == 'yes'

        # Prevent duplicate review for same product
        existing_review = USER_PRODUCT.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()

        if existing_review:
            return "You already reviewed this product."

        # Create new review
        new_review = USER_PRODUCT(
            user_id=user_id,
            product_id=product_id,
            breakout=breakout,
            drying=drying,
            oily=oily,
            hydrating=hydrating,
            heavy=heavy,
            recommend=recommend
        )

        db.session.add(new_review)
        db.session.commit()

        return redirect(url_for('dashboard'))

    # GET = show review page
    products = PRODUCT.query.all()

    return render_template(
        'add_review.html',
        products=products
    )

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json

    email = data.get('user_email')
    password = data.get('user_passwd')

    user = APP_USER.query.filter_by(user_email=email).first()

    if user and check_password_hash(user.user_passwd, password):
        return jsonify({
            "status": "success",
            "user_id": user.user_id,
            "email": user.user_email
        })
    
    return jsonify({"status": "fail"}), 401

if __name__ == "__main__":
    #app.run(debug = True)
    # this allows for all devices connected to the same ip to connect can prompt on my phone
    # used port 8000 and port 5000 was in use only two ports are safe
    app.run(host ="0.0.0.0", port = 8000, debug = True )






