from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from flask_mysqldb import MySQLdb
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
global MySQL
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Konfigurasi Upload Gambar
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Konfigurasi Database
app.config.from_pyfile('config.py')
mysql = MySQL(app)

def get_locations():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT DISTINCT location FROM cars")
    locations = cur.fetchall()
    cur.close()
    return locations

@app.route('/', methods=['GET', 'POST'])
def landing_page():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT DISTINCT location FROM cars")
    locations = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        location = request.form['location']
        start_date = request.form['start_date']
        start_time = request.form['start_time']
        end_date = request.form['end_date']
        end_time = request.form['end_time']

        # Redirect ke search_results, kirim parameter
        return redirect(url_for('search_results', location=location, start_date=start_date, start_time=start_time, end_date=end_date, end_time=end_time))

    return render_template('home.html', locations=locations, register_error='', login_error='')





def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/search_results')
def search_results():
    location = request.args.get('location')
    start_date = request.args.get('start_date')
    start_time = request.args.get('start_time', '00:00')
    end_date = request.args.get('end_date')
    end_time = request.args.get('end_time', '23:59')

    start_datetime = f"{start_date} {start_time}"
    end_datetime = f"{end_date} {end_time}"

    # Filter tambahan
    category = request.args.get('category')
    seats = request.args.get('seats', type=int)
    transmission = request.args.get('transmission')
    sort = request.args.get('sort')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)

    # Status yang harus di filter
    status_filter = ('pending', 'approved', 'ongoing')
    placeholders = ','.join(['%s'] * len(status_filter))  # buat jadi %s,%s,%s

    query = f"""
        SELECT * FROM cars 
        WHERE location = %s 
        AND availability_status = 'Available'
        AND id NOT IN (
            SELECT car_id FROM rentals 
            WHERE status IN ({placeholders})
            AND (
                (%s BETWEEN start_date AND end_date)
                OR (%s BETWEEN start_date AND end_date)
                OR (start_date BETWEEN %s AND %s)
                OR (end_date BETWEEN %s AND %s)
            )
        )
    """

    params = [location] + list(status_filter) + [start_datetime, end_datetime, start_datetime, end_datetime, start_datetime, end_datetime]

    # Tambahan filter
    if category and category != "all":
        query += " AND category = %s"
        params.append(category)
    if seats and seats != "all":
        query += " AND seats = %s"
        params.append(int(seats))
    if transmission and transmission != "all":
        query += " AND transmission = %s"
        params.append(transmission)
    if min_price:
        query += " AND price >= %s"
        params.append(min_price)
    if max_price:
        query += " AND price <= %s"
        params.append(max_price)

    # Sorting harga
    if sort == 'price_low':
        query += " ORDER BY price ASC"
    elif sort == 'price_high':
        query += " ORDER BY price DESC"

    # Eksekusi query
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(query, tuple(params))
    cars = cur.fetchall()
    cur.close()

    # Data filter dropdown
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT DISTINCT category FROM cars")
    categories = [row['category'] for row in cur.fetchall()]
    cur.execute("SELECT DISTINCT seats FROM cars ORDER BY seats ASC")
    seats_options = [row['seats'] for row in cur.fetchall()]
    cur.close()

    return render_template('search_results.html', 
                            cars=cars, 
                            categories=categories, 
                            seats_options=seats_options, 
                            location=location, 
                            start_date=start_date, 
                            start_time=start_time, 
                            end_date=end_date, 
                            end_time=end_time)

    
# Registrasi Member
@app.route('/register', methods=['POST'])
def register():
    gender = request.form['gender']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    birth_date = request.form['birth_date']
    email = request.form['email']
    country_code = request.form['country_code']
    phone_number = request.form['phone_number']
    country = request.form['country']
    address = request.form['address']
    postal_code = request.form['postal_code']
    username = request.form['username']
    password = generate_password_hash(request.form['password'])
    confirm_password = request.form['confirm_password']

    # Simple validasi password sama
    if request.form['password'] != confirm_password:
        return "Password tidak sama, ulangi!"

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO users 
        (username, password, role, gender, first_name, last_name, birth_date, email, country_code, phone_number, country, address, postal_code) 
        VALUES (%s, %s, 'member', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, 
        (username, password, gender, first_name, last_name, birth_date, email, country_code, phone_number, country, address, postal_code))
    mysql.connection.commit()
    cur.close()

    # Auto-login setelah register
    session['user_id'] = cur.lastrowid
    session['username'] = username
    session['role'] = 'member'

    return redirect(url_for('landing_page'))

# Login Member/Admin
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    from_page = request.form.get('from_page')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user[2], password):
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['role'] = user[3]

        # Simpan parameter yang diperlukan dalam session
        if from_page == 'search_results':
            session['location'] = request.form['location']
            session['start_date'] = request.form['start_date']
            session['start_time'] = request.form['start_time']
            session['end_date'] = request.form['end_date']
            session['end_time'] = request.form['end_time']
            return redirect(url_for('search_results',
                                    location=session['location'],
                                    start_date=session['start_date'],
                                    start_time=session['start_time'],
                                    end_date=session['end_date'],
                                    end_time=session['end_time']))
        if user[3] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('landing_page'))

    # LOGIN GAGAL → ambil locations lagi
    locations = get_locations()
    error_msg = "Username atau Password salah!"

    if from_page == 'search_results':
        return render_template('search_results.html', login_error=error_msg,
                                location=request.form['location'],
                                start_date=request.form['start_date'],
                                start_time=request.form['start_time'],
                                end_date=request.form['end_date'],
                                end_time=request.form['end_time'])
    return render_template('home.html', locations=locations, login_error=error_msg, register_error='')



# Dashboard Admin
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' in session and session['role'] == 'admin':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Ambil data mobil + availability_status
        cur.execute("SELECT id, brand, model, year, category, price, transmission, seats, availability_status, image_url FROM cars")
        cars = cur.fetchall()

        # Ambil penyewaan pending
        cur.execute("""SELECT r.id, r.request_date, u.username, c.model, r.start_date, r.end_date 
                        FROM rentals r 
                        JOIN users u ON r.user_id = u.id 
                        JOIN cars c ON r.car_id = c.id 
                        WHERE r.status = 'pending'""")
        pending_rentals = cur.fetchall()

        # Jadwal penyewaan
        cur.execute("""SELECT r.id, r.request_date, u.username, c.model, r.start_date, r.end_date 
                        FROM rentals r 
                        JOIN users u ON r.user_id = u.id 
                        JOIN cars c ON r.car_id = c.id 
                        WHERE r.status = 'approved'""")
        scheduled_rentals = cur.fetchall()

        # Penyewaan berjalan
        cur.execute("""SELECT r.id, u.username, c.model, r.start_date, r.end_date 
                        FROM rentals r 
                        JOIN users u ON r.user_id = u.id 
                        JOIN cars c ON r.car_id = c.id 
                        WHERE r.status = 'ongoing'""")
        ongoing_rentals = cur.fetchall()

        cur.close()
        return render_template('admin_dashboard.html', cars=cars, 
                                pending_rentals=pending_rentals,
                                scheduled_rentals=scheduled_rentals,
                                ongoing_rentals=ongoing_rentals)
    return redirect(url_for('login'))




# Dashboard User
@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'user_id' in session and session['role'] == 'member':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Default query
        query = "SELECT id, brand, model, year, category, price, image_url FROM cars WHERE 1=1"
        params = []

        # Filter brand
        brand = request.args.get('brand')
        if brand and brand != 'all':
            query += " AND brand = %s"
            params.append(brand)

        # Filter category
        category = request.args.get('category')
        if category and category != 'all':
            query += " AND category = %s"
            params.append(category)

        # Filter year
        year = request.args.get('year')
        if year:
            query += " AND year = %s"
            params.append(year)

        # Filter harga min/max
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        if min_price:
            query += " AND price >= %s"
            params.append(min_price)
        if max_price:
            query += " AND price <= %s"
            params.append(max_price)

        # Sorting
        sort = request.args.get('sort')
        if sort == 'az':
            query += " ORDER BY brand ASC"
        elif sort == 'za':
            query += " ORDER BY brand DESC"
        elif sort == 'price_low':
            query += " ORDER BY price ASC"
        elif sort == 'price_high':
            query += " ORDER BY price DESC"

        cur.execute(query, tuple(params))
        cars_list = cur.fetchall()
        cur.close()
        return render_template('user_dashboard.html', cars=cars_list)
    return redirect(url_for('login'))


@app.route('/logout', methods=['POST'])
def logout():
    role = session.get('role')
    session.clear()
    if role == 'admin':
        return redirect(url_for('landing_page'))  # Admin selalu balik ke home
    else:
        return redirect(request.referrer or url_for('landing_page'))  # Member tetap ke halaman sebelumnya


# Manajemen Mobil (Admin)
@app.route('/add_car', methods=['POST'])
def add_car():
    if 'user_id' in session and session['role'] == 'admin':
        brand = request.form['brand']
        model = request.form['model']
        year = request.form['year']
        category = request.form['category']
        transmission = request.form['transmission']
        seats = request.form['seats']
        price = request.form['price']
        location = request.form['location']
        availability_status = request.form['availability_status']
        image = request.files['image']

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(file_path)
            relative_path = f"uploads/{filename}"

            cur = mysql.connection.cursor()
            cur.execute("""
            INSERT INTO cars (brand, model, year, category, price, location, availability_status, transmission, seats, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (brand, model, year, category, price, location, availability_status, transmission, seats, relative_path))
            mysql.connection.commit()
            cur.close()
    return redirect(url_for('admin_dashboard'))



@app.route('/delete_car/<int:car_id>', methods=['POST'])
def delete_car(car_id):
    if 'user_id' in session and session['role'] == 'admin':
        cur = mysql.connection.cursor()
        
        # Ambil path gambar sebelum menghapus mobil
        cur.execute("SELECT image_url FROM cars WHERE id = %s", (car_id,))
        car = cur.fetchone()

        if car and os.path.exists(car[0]):  # Hapus file gambar jika ada
            os.remove(car[0])

        # Hapus mobil dari database
        cur.execute("DELETE FROM cars WHERE id = %s", (car_id,))
        mysql.connection.commit()
        cur.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/confirm_rental', methods=['POST'])
def confirm_rental():
    if 'user_id' not in session or session['role'] != 'member':
        return redirect(url_for('login'))

    user_id = session['user_id']
    car_id = request.form['car_id']
    start_date = request.form['start_date'] + " " + request.form['start_time']
    end_date = request.form['end_date'] + " " + request.form['end_time']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO rentals (user_id, car_id, start_date, end_date, status) VALUES (%s, %s, %s, %s, 'pending')",
                (user_id, car_id, start_date, end_date))
    mysql.connection.commit()
    cur.close()

    flash('Penyewaan berhasil diajukan! Tunggu konfirmasi dari admin.', 'success')
    return redirect(url_for('history'))



@app.route('/rental_confirmation/<int:car_id>', methods=['POST'])
def rental_confirmation(car_id):
    if 'user_id' not in session or session['role'] != 'member':
        return redirect(url_for('login'))

    user_id = session['user_id']
    start_date = request.form['start_date']
    start_time = request.form.get('start_time', '00:00')
    end_date = request.form['end_date']
    end_time = request.form.get('end_time', '00:00')

    # Ambil detail user
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT first_name, last_name, email, phone_number, address FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()

    # Ambil detail mobil
    cur.execute("SELECT id, brand, model, year, category, transmission, seats, price, location, image_url FROM cars WHERE id = %s", (car_id,))
    car_data = cur.fetchone()
    cur.close()

    # Hitung total hari & total harga
    from datetime import datetime
    start_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
    total_days = (end_dt - start_dt).days + 1
    total_price = total_days * car_data['price']

    return render_template('rental_confirmation.html', user=user_data, car=car_data,
                            start_date=start_date, start_time=start_time,
                            end_date=end_date, end_time=end_time,
                            total_days=total_days, total_price=total_price)

@app.route('/get_rental_detail/<int:rental_id>/<status>')
def get_rental_detail(rental_id, status):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT r.id AS rental_id, r.status, r.start_date, r.end_date, 
                u.username, u.email, u.phone_number, u.address,
                c.brand, c.model, c.year, c.transmission, c.seats, c.image_url
        FROM rentals r
        JOIN users u ON r.user_id = u.id
        JOIN cars c ON r.car_id = c.id
        WHERE r.id = %s
    """, (rental_id,))
    detail = cur.fetchone()
    cur.close()

    return render_template('rental_detail_modal.html', detail=detail, status=status)


@app.route('/update_rental_status/<int:rental_id>', methods=['POST'])
def update_rental_status(rental_id):
    new_status = request.form['new_status']

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Ambil car_id dulu
    cur.execute("SELECT car_id FROM rentals WHERE id = %s", (rental_id,))
    rental = cur.fetchone()

    if rental:
        car_id = rental['car_id']

        # Update status rental
        cur.execute("UPDATE rentals SET status = %s WHERE id = %s", (new_status, rental_id))

        # Kalau status 'approved' atau 'ongoing', set mobil Unavailable
        if new_status in ['approved', 'ongoing']:
            cur.execute("UPDATE cars SET availability_status = 'Unavailable' WHERE id = %s", (car_id,))
        # Kalau status selesai, rejected, atau dibatalkan, mobil Available
        elif new_status in ['rejected', 'Selesai', 'Dibatalkan']:
            cur.execute("UPDATE cars SET availability_status = 'Available' WHERE id = %s", (car_id,))
        
        mysql.connection.commit()
        cur.close()

    else:
        # rental_id ga ketemu
        flash('Rental tidak ditemukan!', 'danger')
        return redirect(url_for('admin_dashboard'))

    return redirect(url_for('admin_dashboard'))


# Admin Menyetujui Penyewaan
@app.route('/approve_rental/<int:rental_id>')
def approve_rental(rental_id):
    if 'user_id' in session and session['role'] == 'admin':
        cur = mysql.connection.cursor()
        cur.execute("UPDATE rentals SET status = 'approved' WHERE id = %s", (rental_id,))
        cur.execute("UPDATE cars SET availability_status = 'Unavailable' WHERE id = %s", (car_id,))
        mysql.connection.commit()
        cur.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/notification')
def notification():
    if 'user_id' in session and session['role'] == 'member':
        user_id = session['user_id']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT rentals.id, cars.brand, cars.model, rentals.status, rentals.start_date, rentals.end_date
            FROM rentals
            JOIN cars ON rentals.car_id = cars.id
            WHERE rentals.user_id = %s
            ORDER BY rentals.id DESC
        """, (user_id,))
        notifications = cur.fetchall()
        cur.close()
        return render_template('notification.html', notifications=notifications)
    return redirect(url_for('login'))

@app.route('/admin/transaction_history')
def admin_transaction_history():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Filter input
    selected_brand = request.args.get('brand')
    selected_city = request.args.get('city')
    selected_date = request.args.get('date')
    sort_order = request.args.get('sort', 'latest')

    # Base Query
    query = """
        SELECT r.id AS rental_id, c.brand, c.model, c.year, c.image_url, 
                c.location, u.username, u.email, r.start_date, r.end_date
        FROM rentals r
        JOIN cars c ON r.car_id = c.id
        JOIN users u ON r.user_id = u.id
        WHERE r.status = 'Completed'
    """
    params = []

    # Filter Brand
    if selected_brand:
        query += " AND c.brand = %s"
        params.append(selected_brand)

    # Filter City
    if selected_city:
        query += " AND c.location = %s"
        params.append(selected_city)

    # Filter Date
    if selected_date:
        query += " AND DATE(r.end_date) = %s"
        params.append(selected_date)

    # Sort
    if sort_order == 'oldest':
        query += " ORDER BY r.end_date ASC"
    else:
        query += " ORDER BY r.end_date DESC"

    cur.execute(query, tuple(params))
    transactions = cur.fetchall()

    # Ambil brand & kota unik buat dropdown filter
    cur.execute("SELECT DISTINCT brand FROM cars")
    brands = [row['brand'] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT location FROM cars")
    cities = [row['location'] for row in cur.fetchall()]

    cur.close()

    return render_template('admin_history_transaction.html',
                            transactions=transactions,
                            brands=brands,
                            cities=cities)



@app.route('/admin/history_detail/<int:transaction_id>')
def admin_history_detail(transaction_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT r.id, u.username, u.email, u.phone_number, u.address,
                c.brand, c.model, c.year, c.transmission, c.seats, c.location, c.price,
                r.start_date, r.end_date
        FROM rentals r
        JOIN users u ON r.user_id = u.id
        JOIN cars c ON r.car_id = c.id
        WHERE r.id = %s
    """, (transaction_id,))
    detail = cur.fetchone()
    cur.close()

    return render_template('admin_history_detail_modal.html', detail=detail)

@app.route('/save_transaction', methods=['POST'])
def save_transaction():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    email = request.form['email']
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO transaction_history (user_id, email, status) VALUES (%s, %s, 'pending')", (user_id, email))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('transaction_history'))

@app.route('/history')
def history():
    if not session.get('user_id') or session.get('role') != 'member':
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        cur.execute("""
            SELECT r.id AS booking_id, 
                    c.brand, 
                    c.model, 
                    c.year, 
                    c.transmission, 
                    c.seats, 
                    c.location, 
                    c.image_url, 
                    r.start_date, 
                    r.end_date, 
                    r.status 
            FROM rentals r
            JOIN cars c ON r.car_id = c.id
            WHERE r.user_id = %s
            ORDER BY r.id DESC
        """, (user_id,))

        history_data = list(cur.fetchall())  # Ubah dari tuple ke list
        print("Data history yang diambil:", history_data)  # Debugging

        if not history_data:
            print("User belum pernah melakukan rental!")

    except Exception as e:
        print(f"Error mengambil data history: {e}")
        history_data = []

    finally:
        cur.close()

    return render_template('history.html', history=history_data)

# Route handle pembatalan pemesanan
@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    if 'user_id' not in session or session['role'] != 'member':
        return redirect(url_for('login'))

    booking_id = request.form['booking_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT car_id FROM rentals WHERE id = %s AND user_id = %s", (booking_id, session['user_id']))
    car = cur.fetchone()

    if car:
        car_id = car[0]

        # Update status rental jadi canceled
        cur.execute("UPDATE rentals SET status = 'canceled' WHERE id = %s", (booking_id,))

        # Set mobil jadi available lagi
        cur.execute("UPDATE cars SET availability_status = 'Available' WHERE id = %s", (car_id,))

        mysql.connection.commit()

    cur.close()
    return redirect(url_for('history'))


@app.route('/reject_rental/<int:rental_id>')
def reject_rental(rental_id):
    if 'user_id' in session and session['role'] == 'admin':
        cur = mysql.connection.cursor()
        cur.execute("UPDATE rentals SET status = 'rejected' WHERE id = %s", (rental_id,))
        mysql.connection.commit()
        cur.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/update_car_status/<int:car_id>', methods=['POST'])
def update_car_status(car_id):
    if 'user_id' in session and session['role'] == 'admin':
        new_car_status = request.form['availability_status']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE cars SET availability_status = %s WHERE id = %s", (new_car_status, car_id))
        mysql.connection.commit()
        cur.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_car/<int:car_id>', methods=['POST'])
def edit_car(car_id):
    if 'user_id' in session and session['role'] == 'admin':
        new_price = request.form['price']
        
        # Ambil data mobil sebelum diubah
        cur = mysql.connection.cursor()
        cur.execute("SELECT image_url FROM cars WHERE id = %s", (car_id,))
        car = cur.fetchone()
        cur.close()

        if not car:
            return "Mobil tidak ditemukan"
        
        # Cek apakah admin mengunggah gambar baru
        new_image_url = car[0]  # Gunakan gambar lama sebagai default
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)  # Simpan file baru
                    
                    # Hapus gambar lama jika ada
                    if os.path.exists(car[0]):
                        os.remove(car[0])
                    
                    new_image_url = file_path  # Simpan path gambar baru

        # Update database dengan harga dan gambar baru
        cur = mysql.connection.cursor()
        cur.execute("UPDATE cars SET price = %s, image_url = %s WHERE id = %s", 
                    (new_price, new_image_url, car_id))
        mysql.connection.commit()
        cur.close()

    return redirect(url_for('admin_dashboard'))




if __name__ == '__main__':
    app.run(debug=True)