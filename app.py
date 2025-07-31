import re
import random
import string
from flask import Flask, redirect, render_template, request, flash, session, url_for
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import cloudinary
import cloudinary.uploader
import os
import ssl
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(days=7)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')


ca_cert_path = os.path.join(os.path.dirname(__file__), 'ca.pem')

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'ssl_ca': ca_cert_path,
        'ssl_disabled': False 
    }
}

app.config['CLOUDINARY_CLOUD_NAME'] = os.getenv('CLOUDINARY_CLOUD_NAME')
app.config['CLOUDINARY_API_KEY'] = os.getenv('CLOUDINARY_API_KEY')
app.config['CLOUDINARY_API_SECRET'] = os.getenv('CLOUDINARY_API_SECRET')

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
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    tel = db.Column(db.String(15), nullable=False)

    market = db.relationship('Market', backref='users')

    def __init__(self, name, password, market_id, tel):
        self.name = name
        self.password = password
        self.market_id = market_id
        self.tel = tel


class Market(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marketplace = db.Column(db.String(100), nullable=False)

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
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)

    product = db.relationship('Products', back_populates='reviews')

    def __init__(self, product_id, rating, comment):
        self.product_id = product_id
        self.rating = rating
        self.comment = comment


class ReviewCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    used = db.Column(db.Boolean, default=False)

    user = db.relationship('Users', backref='review_codes')


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
            session['market_id'] = existing_user.market_id
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

    if request.method == 'POST':
        try:
            name = request.form['name'].strip()
            price = request.form['price']
            category = request.form['category']
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

    return render_template('update_product.html', product=product)


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
            selling_unit = request.form['selling_unit']
            image = request.files.get('image')

            if not name:
                flash('Product name is required.', 'error')
                return redirect(url_for('addproduct'))

            if len(name) < 3 or len(name) > 100:
                flash("Product name must be between 3 and 100 characters.", 'error')
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

            market_id = session['market_id']
            product = Products(user_id, name, price, category, market_id, selling_unit, image_url, image_public_id)
            db.session.add(product)
            db.session.commit()

            first_code = generate_unique_review_code(product.id)
            review_code = ReviewCode(code=first_code, user_id=user_id)
            db.session.add(review_code)
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


@app.route('/review/<int:product_id>')
def review(product_id):
    product = Products.query.get_or_404(product_id)
    return render_template('review.html', product=product)


@app.route('/submitrev/<int:product_id>', methods=['POST'])
def submitrev(product_id):
    if request.method == 'POST':
        code = request.form['review_code']
        rating = request.form['rating']
        comment = request.form['comment']

        product = Products.query.get_or_404(product_id)
        review_code = ReviewCode.query.filter_by(code=code, used=False).first()

        if not review_code:
            flash('That code is invalid or already used!', 'error')
            return redirect(url_for('review', product_id=product_id))

        if review_code.user_id != product.user_id:
            flash("This code is not valid for this seller’s product.", 'error')
            return redirect(url_for('review', product_id=product_id))

        review_code.used = True
        new_review = Review(product_id=product.id, rating=int(rating), comment=comment)
        db.session.add(new_review)

        code_str = generate_unique_review_code(review_code.user_id)
        new_code = ReviewCode(code=code_str, user_id=review_code.user_id, used=False)
        db.session.add(new_code)
        db.session.commit()
        flash('Thank you for your review!', 'success')
        return redirect(url_for('review', product_id=product_id))
    return redirect(url_for('review'), product_id=product_id)


@app.route('/ufeed')
def ufeed():
    if 'user' in session:
        uname = session['user']
        user_id = session['user_id']
        user = Users.query.get(user_id)

        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('logout'))

        latest_code = ReviewCode.query.filter_by(used=False, user_id=user_id).order_by(ReviewCode.id.desc()).first()
        review_code = latest_code.code if latest_code else "No review code available"

        product_ids = [p.id for p in user.products]
        reviews = Review.query.filter(Review.product_id.in_(product_ids)).order_by(Review.id.desc()).all()

        return render_template('user_feedback.html', content=uname, review_code=review_code, reviews=reviews)
    else:
        flash('You need to login first!', 'error')
        return redirect(url_for('login'))


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session:
        flash('You need to login first!', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = Users.query.get_or_404(user_id)
    market = Market.query.get(user.market_id)

    if request.method == 'POST' and 'delete' in request.form:
        try:
            # Delete all products and their images
            products = Products.query.filter_by(user_id=user_id).all()
            for product in products:
                if product.image_public_id:
                    cloudinary.uploader.destroy(product.image_public_id)
                db.session.delete(product)

            # Delete all review codes
            for review_code in user.review_codes:
                db.session.delete(review_code)

            # Delete all reviews associated with the user's products
            product_ids = [p.id for p in products]
            if product_ids:
                Review.query.filter(Review.product_id.in_(product_ids)).delete()

            # Delete the user
            db.session.delete(user)
            db.session.commit()

            # Clear session
            session.pop('user', None)
            session.pop('user_id', None)
            session.pop('market_id', None)
            flash('Account and all associated data deleted successfully!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting account. Please try again. ({str(e)})', 'error')
            return redirect(url_for('settings'))

    return render_template('settings.html', user=user, market=market)


@app.route('/update_settings', methods=['GET', 'POST'])
def update_settings():
    if 'user' not in session:
        flash('You have to login first', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = Users.query.get_or_404(user_id)
    markets = Market.query.all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '').strip()
        market_id = request.form.get('market_id')

        updated = False

        if name and name != user.name:
            user.name = name
            session['user'] = name
            updated = True

        if password:
            user.password = generate_password_hash(password)
            updated = True

        if market_id and int(market_id) != user.market_id:
            try:
                user.market_id = int(market_id)
                session['market_id'] = user.market_id
                updated = True
            except ValueError:
                flash("Invalid market selected.", 'error')
                return redirect(url_for('update_settings'))

        if updated:
            try:
                db.session.commit()
                flash('Settings updated successfully!', 'success')
                return redirect(url_for('settings'))
            except Exception as e:
                db.session.rollback()
                flash('Error updating settings. Please try again.', 'error')
        else:
            flash('No changes made.', 'info')

    return render_template('update_settings.html', user=user, markets=markets)


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    session.pop('market_id', None)
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
    markets = Market.query.all()

    if request.method == 'POST':
        uname = request.form['names'].strip()
        pswd = request.form['password']
        tel = request.form['tel']
        marketplace_str = request.form.get('market_id')
        confpass = request.form['confpass']

        if pswd != confpass:
            flash("Passwords don't match.", "error")
            return redirect(url_for('register'))

        if not re.fullmatch(r'^07\d{8}$', tel):
            flash("Phone number must start with 07 and be 10 digits long.", "error")
            return redirect(url_for('register'))

        if not marketplace_str or marketplace_str.strip() == "":
            flash("Please select a valid market.", "error")
            return redirect(url_for('register'))

        try:
            marketplace = int(marketplace_str)
        except (ValueError, TypeError):
            flash("Invalid market selection.", "error")
            return redirect(url_for('register'))

        existing_user = Users.query.filter_by(name=uname).first()

        if existing_user:
            flash("Username taken. Choose a different one.", "error")
            return redirect(url_for('register'))

        hashed_pass = generate_password_hash(pswd, method='pbkdf2:sha256')
        usr = Users(uname, hashed_pass, marketplace, tel)

        db.session.add(usr)
        db.session.commit()
        flash("You are registered!", "success")
        return redirect(url_for('login'))

    else:
        return render_template('register.html', markets=markets)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()