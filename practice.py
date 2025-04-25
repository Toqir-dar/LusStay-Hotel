from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pharmacy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

db = SQLAlchemy(app)

# Models
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'pharmacist', 'cashier'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Medicine(db.Model):
    medicine_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100))
    category = db.Column(db.String(50))
    quantity_in_stock = db.Column(db.Integer, default=0)
    price = db.Column(db.Numeric(10,2), nullable=False)
    expiry_date = db.Column(db.Date)
    batch_number = db.Column(db.String(50))

class Supplier(db.Model):
    supplier_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100))
    address = db.Column(db.Text)

class Purchase(db.Model):
    purchase_id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.supplier_id'))
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.medicine_id'))
    quantity = db.Column(db.Integer, nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    cost_price = db.Column(db.Numeric(10,2), nullable=False)

class Sale(db.Model):
    sale_id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.medicine_id'))
    quantity_sold = db.Column(db.Integer, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Numeric(10,2), nullable=False)
    sold_by = db.Column(db.Integer, db.ForeignKey('user.user_id'))

class Customer(db.Model):
    customer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/medicines')
def show_medicines():
    medicines = Medicine.query.all()
    return render_template('medicines.html', medicines=medicines)

@app.route('/add-medicine', methods=['GET', 'POST'])
def add_medicine():
    if request.method == 'POST':
        name = request.form['name']
        brand = request.form['brand']
        category = request.form['category']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        expiry_date = request.form['expiry_date']
        batch_number = request.form['batch_number']

        new_med = Medicine(
            name=name,
            brand=brand,
            category=category,
            quantity_in_stock=quantity,
            price=price,
            expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d'),
            batch_number=batch_number
        )
        db.session.add(new_med)
        db.session.commit()
        return redirect(url_for('show_medicines'))
    return render_template('add_medicine.html')

@app.route('/sales', methods=['GET', 'POST'])
def handle_sales():
    if request.method == 'POST':
        medicine_id = request.form['medicine_id']
        quantity_sold = int(request.form['quantity_sold'])
        sold_by = int(request.form['sold_by'])

        medicine = Medicine.query.get(medicine_id)
        if medicine and medicine.quantity_in_stock >= quantity_sold:
            total_price = float(medicine.price) * quantity_sold
            medicine.quantity_in_stock -= quantity_sold
            sale = Sale(medicine_id=medicine_id, quantity_sold=quantity_sold, sold_by=sold_by, total_price=total_price)
            db.session.add(sale)
            db.session.commit()
            return redirect(url_for('handle_sales'))
        else:
            return "Not enough stock or invalid medicine ID", 400

    sales = Sale.query.all()
    return render_template('sales.html', sales=sales)

@app.route('/purchases', methods=['GET', 'POST'])
def handle_purchases():
    if request.method == 'POST':
        supplier_id = int(request.form['supplier_id'])
        medicine_id = int(request.form['medicine_id'])
        quantity = int(request.form['quantity'])
        cost_price = float(request.form['cost_price'])

        purchase = Purchase(supplier_id=supplier_id, medicine_id=medicine_id,
                            quantity=quantity, purchase_date=datetime.today(), cost_price=cost_price)
        medicine = Medicine.query.get(medicine_id)
        if medicine:
            medicine.quantity_in_stock += quantity
            db.session.add(purchase)
            db.session.commit()
            return redirect(url_for('handle_purchases'))
        else:
            return "Invalid medicine ID", 400

    purchases = Purchase.query.all()
    return render_template('purchases.html', purchases=purchases)

if __name__ == '__main__':
    app.run(debug=True)