import re
import random
import string
from flask import Flask, redirect, render_template, request, flash, session, url_for
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = ''
app.permanent_session_lifetime = timedelta(days=7)
app.config['SQLALCHEMY_DATABASE_URI'] = ''
app.config['CLOUDINARY_CLOUD_NAME'] = ''
app.config['CLOUDINARY_API_KEY'] = ''
app.config['CLOUDINARY_API_SECRET'] = ''

cloudinary.config(
    cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
    api_key=app.config['CLOUDINARY_API_KEY'],
    api_secret=app.config['CLOUDINARY_API_SECRET']
)

db = SQLAlchemy(app)


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tel = db.Column(db.String(15), nullable=False)

    def __init__(self, name, password, tel):
        self.name = name
        self.password = password
        self.tel = tel

class Market(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marketplace = db.Column(db.String, nullable=False)

    def __init__(self, marketplace):
        self.marketplace = marketplace

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    selling_unit = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    image_public_id = db.Column(db.String(200), nullable=False)

    market = db.relationship('Market', backref='products')
    user = db.relationship('Users', backref='products')
    reviews = db.relationship('Review', back_populates='product', lazy=True)

    def __init__(self, user_id, name, price, category, market_id, selling_unit, image_url, image_public_id):
        self.user_id = user_id
        self.name = name
        self.price = price
        self.category = category
        self.market_id = market_id
        self.selling_unit = selling_unit
        self.image_url = image_url
        self.image_public_id = image_public_id

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)

    product = db.relationship('Products', back_populates='reviews')

class ReviewCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    used = db.Column(db.Boolean, default=False)

    product = db.relationship('Product', backref='review_codes')

def generate_unique_review_code(product_id):
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        existing = ReviewCode.query.filter_by(code=code).first()
        if not existing:
            return code

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'user' in session:
        flash('You are already logged in.', 'info')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        session.permanent = True
        uname = request.form['names']
        pswd = request.form['password']

        existing_user = Users.query.filter_by(name=uname).first()

        if existing_user and check_password_hash(existing_user.password, pswd):
            session['user'] = uname
            session['user_id'] = existing_user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Username or Password', 'error')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        uname = session['user']
        user_id = session['user_id']
        products = Products.query.filter_by(user_id=user_id).all()

        return render_template('product.html', content=uname, products=products)
    else:
        flash('You need to login first!', 'error')
        return redirect(url_for('login'))
    
@app.route('/products', methods=['GET'])
def products():
    category = request.args.get('category')
    marketplace = request.args.get('marketplace')

    query = Products.query

    if category:
        query = query.filter(Products.category == category)

    if marketplace:
        query = query.join(Market).filter(Market.marketplace == marketplace)

    prods = query.all()

    categories = db.session.query(Products.category).distinct().all()
    marketplaces = db.session.query(Market.marketplace).distinct().all()

    return render_template('products.html', products=prods, categories=[c[0] for c in categories], marketplaces=[m[0] for m in marketplaces])

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    prds = Products.query.get_or_404(product_id)

    return render_template('product_detail.html', product=prds)
    
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_product(id):
    if 'user' not in session:
        flash('You need to login first!', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    product = Products.query.get_or_404(id)

    if product.user_id != user_id:
        flash("You don't have permission to edit this product.", 'error')
        return redirect(url_for('dashboard'))
    
    markets = Market.query.all()

    if request.method == 'POST':
        try:
            name = request.form['name'].strip()
            price = request.form['price']
            category = request.form['category']
            market_id = request.form['market_id']
            selling_unit = request.form['selling_unit']
            image = request.files.get('image')

            if not name:
                flash('Product name is required.', 'error')
                return redirect(url_for('update_product', id=id))

            try:
                price = float(price)
                if price < 0:
                    flash('Price cannot be negative.', 'error')
                    return redirect(url_for('update_product', id=id))
            except ValueError:
                flash('Price must be a valid number.', 'error')
                return redirect(url_for('update_product', id=id))

            product.name = name
            product.price = price
            product.category = category
            product.market_id = market_id
            product.selling_unit = selling_unit

            if image and image.filename != '':
                cloudinary.uploader.destroy(product.image_public_id)
                upload_result = cloudinary.uploader.upload(image, folder='isokoinfo_products')
                product.image_url = upload_result['secure_url']
                product.image_public_id = upload_result['public_id']

            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('update_product', id=id))

    return render_template('update_product.html', product=product, markets=markets)

@app.route('/addproduct', methods=['GET', 'POST'])
def addproduct():
    if 'user' not in session:
        flash('You need to login first!', 'error')
        return redirect(url_for('login'))
    
    uname = session['user']
    markets = Market.query.all()
    
    if request.method == 'POST':
        try:
            user_id = session['user_id']
            name = request.form['name'].strip()
            price = request.form['price']
            category = request.form['category']
            market_id = request.form['market_id']
            selling_unit = request.form['selling_unit']
            image = request.files.get('image')

            if not name:
                flash('Product name is required.', 'error')
                return redirect(url_for('addproduct'))
            
            try:
                price = float(price)
                if price < 0:
                    flash('Price cannot be negative.', 'error')
                    return redirect(url_for('addproduct'))
            except ValueError:
                flash('Price must be a valid number.', 'error')
                return redirect(url_for('addproduct'))
            
            if not image or image.filename == '':
                flash('Product image is required.', 'error')
                return redirect(url_for('addproduct'))

            upload_result = cloudinary.uploader.upload(image, folder='isokoinfo_products')
            image_url = upload_result['secure_url']
            image_public_id = upload_result['public_id']
            
            product = Products(user_id, name, price, category, market_id, selling_unit, image_url, image_public_id)
            db.session.add(product)
            db.session.commit()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('addproduct'))
    
    return render_template('add_product.html', content=uname, markets=markets)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    if 'user' not in session:
        flash('You must be logged in to delete products.', 'error')
        return redirect(url_for('login'))
    user_id = session['user_id']
    product = Products.query.get_or_404(id)

    if product.user_id != user_id:
        flash("You don't have permission to delete this product.", 'error')
        return redirect(url_for('dashboard'))

    try:
        cloudinary.uploader.destroy(product.image_public_id)
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted!', 'success')
    except:
        db.session.rollback()
        flash('Error deleting product!', 'error')

    return redirect(url_for('dashboard'))

@app.route('/review')
def review():
    return render_template('review.html')

@app.route('/submitrev', methods=['POST', 'GET'])
def submitrev():
    if request.method == 'POST':
        code = request.form['review_code']
        rating = request.form['rating']
        comment = request.form['comment']

        review_code = ReviewCode.query.filter_by(code=code, used=False).first()
        prorevid = review_code.product_id

        if not review_code:
            flash('That code is invalid or already used!', 'error')
            return redirect(url_for('review'))
        
        new_rev = Review(prorevid, int(rating), comment)
        db.session.add(new_rev)
        db.session.commit()
        flash('Thanks you for the review!', 'success')
        return(url_for('products'))
        
    return render_template('review')

@app.route('/ufeed')
def ufeed():
    if 'user' in session:
        uname = session['user']
        return render_template('user_feedback.html', content=uname)
    else:
        flash('You need to login first!', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    flash('Logged Out', 'success')
    return redirect(url_for('login'))

@app.route('/idkbruh', methods=['POST', 'GET'])
def idkbruh():
    if request.method == 'POST':
        mrkt = request.form['location']
        mkt = Market(mrkt)
        db.session.add(mkt)
        db.session.commit()
        flash("Adding it worked!")
        return redirect(url_for('idkbruh'))
    
    else:
        flash("Adding didn't work!")

    return render_template('admin.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        uname = request.form['names']
        pswd = request.form['password']
        tel = request.form['tel']
        confpass = request.form['confpass']

        if pswd != confpass:
            flash("Passwords don't match.", "error")
            return redirect(url_for('register'))
        
        if not re.fullmatch(r'^07\d{8}$', tel):
            flash("Phone number must start with 07 and be 10 digits long.", "error")
            return redirect(url_for('register'))

        existing_user = Users.query.filter_by(name=uname).first()

        if existing_user:
            flash("Username taken. Choose a different one.", "error")
            return redirect(url_for('register'))
        
        hashed_pass = generate_password_hash(pswd, method='pbkdf2:sha256')
        
        usr = Users(uname, hashed_pass, tel)

        db.session.add(usr)
        db.session.commit()
        flash("You are registered!", "success")
        return redirect(url_for('login'))

    else:
        return render_template('register.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

