from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure database and file storage
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///donations.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            points INTEGER DEFAULT 0 
        )
    ''')
    conn.commit()
    conn.close()

init_db()



# Database models
class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_path = db.Column(db.String(200))
    gender = db.Column(db.String(20))  # Example: "Male", "Female", "Unisex"
    size = db.Column(db.String(20))    # Example: "Small", "Medium", "Large"
    kids = db.Column(db.Boolean, default=False)  # True for kids, False otherwise
    item_type = db.Column(db.String(50))  # Example: "Clothing", "Toys", "Books"
    donated = db.Column(db.Boolean, default=False)
    purchased = db.Column(db.Boolean, default=False) 
    location = db.Column(db.String(200))  # New field for location



class Interest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donation.id'), nullable=False)
    viewer_email = db.Column(db.String(100), nullable=False)
    notified = db.Column(db.Boolean, default=False) 

    donation = db.relationship('Donation', backref=db.backref('interests', lazy=True))

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donation.id'), nullable=False)
    viewer_email = db.Column(db.String(100), nullable=False)

    donation = db.relationship('Donation', backref=db.backref('cart_items', lazy=True))

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donation.id'), nullable=False)
    sender_email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    donation = db.relationship('Donation', backref=db.backref('chats', lazy=True))


# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                      (username, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            return "User already exists!"
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        else:
            return "Invalid credentials!"
    
    return render_template('login.html')

@app.route('/index')
def index():
    if 'user_id' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# New route to handle the "Buy" button
@app.route('/buy_item/<int:donation_id>', methods=['POST'])
def buy_item(donation_id):
    if 'user_id' not in session:
        return jsonify({'message': 'Please log in to buy items!'}), 403

    # Get the logged-in user's email
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    conn.close()

    if not user:
        return jsonify({'message': 'User not found!'}), 404

    buyer_email = user[0]

    # Check if the donation exists and is available for purchase
    donation = Donation.query.get(donation_id)
    if not donation:
        return jsonify({'message': 'Donation not found!'}), 404

    if donation.purchased:
        return jsonify({'message': 'This item has already been purchased!'}), 400

    # Mark the donation as purchased
    donation.purchased = True
    db.session.commit()

    return jsonify({'message': 'You have successfully purchased this item!'})


@app.route('/donor', methods=['GET', 'POST'])
def donor():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT email, points FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return redirect(url_for('login'))
    
    donor_email = user[0]
    points = user[1]

    if request.method == 'POST':
        # Existing donation logic
        name = request.form['name']
        description = request.form['description']
        image = request.files['image']
        gender = request.form['gender']
        size = request.form['size']
        kids = bool(request.form.get('kids'))
        item_type = request.form['item_type']
        location = request.form['location']

        image_filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image.save(image_path)

        donation = Donation(
            name=name,
            email=donor_email,
            description=description,
            image_path=image_path,
            gender=gender,
            size=size,
            kids=kids,
            item_type=item_type,
            location=location
        )
        db.session.add(donation)
        db.session.commit()

        return jsonify({'message': 'Donation added successfully!'})

    donation = Donation.query.filter_by(email=donor_email).all()
    donor_count = len(donation)
    interests = Interest.query.join(Donation).filter(Donation.email == donor_email).all()

    return render_template(
        'donor.html',
        donation=donation,
        donor_count=donor_count,
        interests=interests,
        donor_email=donor_email,
        points=points  # Pass reward points to the template
    )


# Update mark_as_donated route to clear the purchased status
@app.route('/mark_as_donated/<int:donation_id>', methods=['POST'])
def mark_as_donated(donation_id):
    if 'user_id' not in session:
        return jsonify({'message': 'Please log in to mark donations as donated!'}), 403

    # Fetch the logged-in user's email
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    conn.close()

    if not user:
        return jsonify({'message': 'User not found!'}), 404

    donor_email = user[0]

    # Fetch the donation
    donation = Donation.query.get(donation_id)
    if not donation:
        return jsonify({'message': 'Donation not found!'}), 404

    # Ensure the logged-in user owns the donation
    if donation.email != donor_email:
        return jsonify({'message': 'Unauthorized action!'}), 403

    # Mark the donation as donated and clear the purchased status
    donation.donated = True
    donation.purchased = False
    db.session.commit()

    # Add reward points to the donor
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET points = points + 10 WHERE email = ?', (donor_email,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Donation marked as donated, and reward points added!'})

# Update the viewer route
@app.route('/viewer', methods=['GET'])
def viewer():
    filters = {}
    gender = request.args.get('gender', '').strip()
    size = request.args.get('size', '').strip()
    kids = request.args.get('kids', '').strip()
    item_type = request.args.get('item_type', '').strip()
    location = request.args.get('location', '').strip().lower()
    search = request.args.get('search', '').strip().lower()  # Lowercase for case-insensitive search

    # Apply filters if provided
    if gender:
        filters['gender'] = gender
    if size:
        filters['size'] = size
    if kids:
        filters['kids'] = kids == 'true'
    if item_type:
        filters['item_type'] = item_type

    # Filter donations
    donations_query = Donation.query.filter_by(donated=False, **filters)

    if location:
        donations_query = donations_query.filter(Donation.location.ilike(f"%{location}%"))
    if search:
        donations_query = donations_query.filter(
            (Donation.name.ilike(f"%{search}%")) | 
            (Donation.description.ilike(f"%{search}%"))
        )

    donations = donations_query.all()

    return render_template('viewer.html', donations=donations)


@app.route('/add_to_cart/<int:donation_id>', methods=['POST'])
def add_to_cart(donation_id):
    if 'user_id' not in session:
        return jsonify({'message': 'Please log in to add items to your cart!'}), 403

    # Fetch the logged-in user's email
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    conn.close()

    if not user:
        return jsonify({'message': 'User not found!'}), 404

    viewer_email = user[0]

    # Check if the donation exists
    donation = Donation.query.get(donation_id)
    if not donation:
        return jsonify({'message': 'Donation not found!'}), 404

    # Check if the item is already in the cart
    existing_cart_item = Cart.query.filter_by(donation_id=donation_id, viewer_email=viewer_email).first()
    if existing_cart_item:
        return jsonify({'message': 'Item already in cart!'}), 400

    # Add the item to the cart
    cart_item = Cart(donation_id=donation_id, viewer_email=viewer_email)
    db.session.add(cart_item)
    db.session.commit()

    return jsonify({'message': 'Item added to cart successfully!'})

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    conn.close()
    
    viewer_email = user[0]
    
    cart_items = Cart.query.filter_by(viewer_email=viewer_email).join(Donation).all()
    return render_template('cart.html', cart_items=cart_items)

@app.route('/remove_from_cart/<int:cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    if 'user_id' not in session:
        return jsonify({'message': 'Please log in to remove items!'}), 403
    
    # Find the cart item
    cart_item = Cart.query.get(cart_id)
    if not cart_item:
        return jsonify({'message': 'Cart item not found!'}), 404
    
    # Ensure the logged-in user owns the item being removed
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    conn.close()
    
    if cart_item.viewer_email != user[0]:
        return jsonify({'message': 'Unauthorized action!'}), 403
    
    # Remove the item
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message': 'Item removed from cart!'})

@app.route('/get_messages/<int:donation_id>', methods=['GET'])
def get_messages(donation_id):
    if 'user_id' not in session:
        return jsonify({'message': 'Please log in to view messages!'}), 403

    messages = Chat.query.filter_by(donation_id=donation_id).order_by(Chat.timestamp.asc()).all()
    messages_data = [
        {'sender_email': chat.sender_email, 'message': chat.message, 'timestamp': chat.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        for chat in messages
    ]
    return jsonify(messages_data)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'message': 'Please log in to send messages!'}), 403

    data = request.get_json()
    donation_id = data['donation_id']
    message_text = data['message']

    # Get sender email
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    conn.close()

    if not user:
        return jsonify({'message': 'User not found!'}), 404

    sender_email = user[0]

    # Save message in the database
    chat = Chat(donation_id=donation_id, sender_email=sender_email, message=message_text)
    db.session.add(chat)
    db.session.commit()

    return jsonify({'message': 'Message sent successfully!'})

# @app.route('/donate', methods=['GET', 'POST'])
# def donate():



#     if 'user_id' not in session:
#         return redirect(url_for('login'))

#     return render_template('donate.html')


# @app.route('/donate_food', methods=['GET', 'POST'])
# def donate_food():
#     """
#     Handles the donation of food items.
#     """
#     if 'user_id' not in session:
#         return redirect(url_for('login'))

#     # Get the logged-in user's email
#     conn = sqlite3.connect('users.db')
#     c = conn.cursor()
#     c.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],))
#     user = c.fetchone()
#     conn.close()

#     if not user:
#         return redirect(url_for('login'))

#     donor_email = user[0]

#     if request.method == 'POST':
#         # Gather form data
#         food_name = request.form['food_name']
#         quantity = request.form['quantity']
#         expiry_date = request.form['expiry_date']
#         location = request.form['location']  # Location of the donor
#         notes = request.form.get('notes', '')

#         # Save the food donation to the database
#         donation = Donation(
#             name=food_name,
#             email=donor_email,
#             description=notes,
#             item_type="Food",
#             location=location,
#             size=quantity,  # Using size field to store quantity (can customize later)
#             gender=None,    # Food donations do not require gender
#             kids=None       # Kids flag is not relevant for food donations
#         )
#         db.session.add(donation)
#         db.session.commit()

#         return jsonify({'message': 'Food donation added successfully!'})

#     return render_template('donate_food.html')


# @app.route('/donate_clothing', methods=['GET', 'POST'])
# def donate_clothing():
#     """
#     Handles the donation of clothing items.
#     """
#     if 'user_id' not in session:
#         return redirect(url_for('login'))

#     # Get the logged-in user's email
#     conn = sqlite3.connect('users.db')
#     c = conn.cursor()
#     c.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],))
#     user = c.fetchone()
#     conn.close()

#     if not user:
#         return redirect(url_for('login'))

#     donor_email = user[0]

#     if request.method == 'POST':
#         # Gather form data
#         name = request.form['name']
#         description = request.form['description']
#         image = request.files['image']
#         gender = request.form['gender']
#         size = request.form['size']
#         kids = bool(request.form.get('kids'))
#         item_type = request.form['item_type']
#         location = request.form['location']  # Location of the donor

#         # Save image to uploads directory
#         image_filename = secure_filename(image.filename)
#         image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
#         image.save(image_path)

#         # Save the clothing donation to the database
#         donation = Donation(
#             name=name,
#             email=donor_email,
#             description=description,
#             image_path=image_path,
#             gender=gender,
#             size=size,
#             kids=kids,
#             item_type=item_type,
#             location=location
#         )
#         db.session.add(donation)
#         db.session.commit()

#         return jsonify({'message': 'Clothing donation added successfully!'})

#     donation = Donation.query.filter_by(email=donor_email).all()
#     donor_count = len(donation)
#     interests = Interest.query.join(Donation).filter(Donation.email == donor_email).all()

#     return render_template('donate_clothing.html',
#                             donation=donation,
#         donor_count=donor_count,
#         interests=interests,
#         donor_email=donor_email)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)