from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from mysql.connector import connect, Error
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'S@kal01012002',
    'database': 'ecommerce'
}

# Connect to MySQL
conn = connect(**mysql_config)
cursor = conn.cursor()

# Routes
@app.route('/')
def index():
    cus_id = request.args.get('cus_id', '')
    if cus_id:
        cursor.execute("select s.ship_id, c.cus_id as ID, c.cus_contact as Contact, s.item_name as Item, s.unit_value as Value, s2.unit_measurement as Measurement, s.service_id as Service, td.recieve_date as RegDate, td.status as Status, t.payment_status as Payment from shipment s join customer c on s.cus_id = c.cus_id join tracking_details td on td.ship_id = s.ship_id join `transaction` t on t.ship_id = s.ship_id join services s2 on s.service_id = s2.service_id WHERE c.cus_id = %s order by td.recieve_date desc", (cus_id,))
    else:
        cursor.execute("select s.ship_id, c.cus_id as ID, c.cus_contact as Contact, s.item_name as Item, s.unit_value as Value, s2.unit_measurement as Measurement, s.service_id as Service, td.recieve_date as RegDate, td.status as Status, t.payment_status as Payment from shipment s join customer c on s.cus_id = c.cus_id join tracking_details td on td.ship_id = s.ship_id join `transaction` t on t.ship_id = s.ship_id join services s2 on s.service_id = s2.service_id order by td.recieve_date desc")
    records = cursor.fetchall()
    return render_template('index.html', records=records, cus_id=cus_id)

@app.route('/add', methods=['POST'])
def add_customer():
    if request.method == 'POST':
        Fname = request.form.get('Fname')
        Lname = request.form.get('Lname')
        email = request.form.get('email')
        contact = request.form.get('contact')
        
        if not Fname or not Lname or not email or not contact:
            missing_fields = [field for field in ['Fname', 'Lname', 'email', 'contact'] if not request.form.get(field)]
            flash(f'Failed to add new Customer : Missing fields {", ".join(missing_fields)}', 'error')
            return redirect(url_for('index'))
    
        try:
            cursor.execute("INSERT INTO customer (cus_Fname, cus_Lname, cus_email, cus_contact) VALUES (%s, %s, %s, %s)", (Fname, Lname, email, contact))
            conn.commit()
            flash(f'Customer {Fname} {Lname} Successfully added', 'success')
        except Exception as e:
            flash(f'Failed to add new Customer : {str(e)}', 'error')

        return redirect(url_for('index'))
    
@app.route('/addorder', methods=['POST'])
def add_order():
    if request.method == 'POST':
        cus_id = request.form.get('cid')
        item = request.form.get('Iname')
        value = request.form.get('val')
        service = request.form.get('service')
        address = request.form.get('address')
        if not cus_id or not item or not value or not service:
            missing_fields = [field for field in ['cid', 'Iname', 'val', 'service'] if not request.form.get(field)]
            flash(f'Failed to add new Order : Missing fields {", ".join(missing_fields)}', 'error')
            return redirect(url_for('index'))
        try:
            cursor.execute("call insert_order(%s, %s, %s, %s, %s)", (cus_id, item, value, service, address))
            conn.commit()
            flash(f'Order Successfully added', 'success')
        except Exception as e:
            flash(f'Failed to add to new order record : {str(e)}', 'error')
            return redirect(url_for('index'))
        
        return redirect(url_for('index'))

@app.route('/update', methods=['POST'])
def update_order():
    if request.method == 'POST':
        ship_id1 = request.form['ship_id']
        cus_id1 = request.form['cus_id']
        item1 = request.form['item']
        value1 = request.form['value']
        service1 = request.form['service']
        status1 = request.form['status']
        payment1 = request.form['payment']
        try:
            # cursor.execute("Call UpdateShippingDetails(%s, %s, %s, %s, %s, %s, %s)", (cus_id1, item1, service1, value1, ship_id1, status1, payment1))
            cursor.callproc('UpdateShippingDetails', 
                        (cus_id1, item1, service1, value1, ship_id1, status1, payment1))
            conn.commit()
            flash(f'Order {ship_id1} Successfully updated', 'success')
        except Error as e:
            flash(f'Failed to update order record : {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/confirm_delete/<int:ship_id>', methods=['POST'])
def delete_order(ship_id):
    try:
        cursor.callproc("DeleteShippingDetails", (ship_id,))
        conn.commit()
        flash(f'Order {ship_id} Successfully deleted', 'success')
    except Error as e:
        flash(f'Failed to delete order : {e}', 'error')
    return redirect(url_for('index'))

@app.route('/get_order/<int:ship_id>')
def get_order(ship_id):
    try:
                cursor.execute("select s.ship_id, c.cus_id, c.cus_contact, s.item_name, s.unit_value, s2.unit_measurement, s.service_id, td.status, td.recieve_date, t.payment_status from shipment s join customer c on s.cus_id = c.cus_id join tracking_details td on td.ship_id = s.ship_id join `transaction` t on t.ship_id = s.ship_id join services s2 on s.service_id = s2.service_id WHERE s.ship_id = %s", (ship_id,))
                record = cursor.fetchone()
                if record:
                    return jsonify({
                        'ship_id': record[0],
                        'cus_id': record[1],
                        'contact': record[2],
                        'item': record[3],
                        'value': record[4],
                        'measurement': record[5],
                        'service': record[6],
                        'registered': record[8],
                        'status': record[7],
                        'payment': record[9]
                    })
                else:
                    return jsonify({'error': 'Record not found'}), 404
    except Error as e:
        print(e)
        flash(f'Failed: {str(e)}', 'error')
        return jsonify({'error': 'Database error'}), 500

if __name__ == '__main__':
    app.run(debug=True)