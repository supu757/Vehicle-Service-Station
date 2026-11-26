from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

customer_bp = Blueprint('customer', __name__)

# 1. Customer Dashboard Route
@customer_bp.route('/customer/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'Customer':
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM vehicles WHERE customer_id = %s ORDER BY vehicle_id DESC", (user_id,))
    vehicles = cursor.fetchall()

    cursor.execute("""
        SELECT a.*, v.license_plate, v.make_model 
        FROM appointments a 
        JOIN vehicles v ON a.vehicle_id = v.vehicle_id 
        WHERE a.customer_id = %s ORDER BY a.booking_date DESC
    """, (user_id,))
    appointments = cursor.fetchall()

    active_service = appointments[0] if appointments else None

    total_vehicles = len(vehicles)
    total_bookings = len(appointments)
    pending_services = sum(1 for app in appointments if app.get('status') == 'Pending')
    completed_services = sum(1 for app in appointments if app.get('status') == 'Completed')

    conn.close()

    return render_template(
        'customer/dashboard.html', 
        vehicles=vehicles, 
        active_service=active_service,
        total_vehicles=total_vehicles,
        total_bookings=total_bookings,
        pending_services=pending_services,
        completed_services=completed_services
    )

# 2. Service History Route
@customer_bp.route('/customer/service-history')
def service_history_page():
    if 'user_id' not in session or session.get('role') != 'Customer':
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.*, v.license_plate, v.make_model, v.colour, v.mileage 
        FROM appointments a 
        JOIN vehicles v ON a.vehicle_id = v.vehicle_id 
        WHERE a.customer_id = %s 
        ORDER BY a.booking_date DESC
    """, (user_id,))
    history = cursor.fetchall()
    conn.close()

    return render_template('customer/service_history.html', history=history)

# 3. Bookings Route
@customer_bp.route('/customer/bookings')
def bookings_page():
    if 'user_id' not in session or session.get('role') != 'Customer':
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.*, v.license_plate, v.make_model, v.colour 
        FROM appointments a 
        JOIN vehicles v ON a.vehicle_id = v.vehicle_id 
        WHERE a.customer_id = %s ORDER BY a.booking_date DESC
    """, (user_id,))
    appointments = cursor.fetchall()
    conn.close()

    return render_template('customer/bookings.html', appointments=appointments)

# 4. Vehicle Registration GET Route
@customer_bp.route('/customer/register-vehicle', methods=['GET'])
def vehicle_registration_page():
    if 'user_id' not in session or session.get('role') != 'Customer':
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('customer/vehicle_registration.html')

# 5. Add Vehicle POST Route (Mileage removed from form -> default 0)
@customer_bp.route('/customer/add-vehicle', methods=['POST'])
def add_vehicle():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    customer_id = session['user_id']
    license_plate = request.form.get('license_plate')
    make_model = request.form.get('make_model')
    chassis_number = request.form.get('chassis_number')
    colour = request.form.get('colour')
    year = request.form.get('year')
    mileage_raw = request.form.get('mileage')
    mileage = int(mileage_raw) if mileage_raw and str(mileage_raw).isdigit() else 0

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO vehicles (customer_id, license_plate, make_model, chassis_number, colour, year, mileage) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (customer_id, license_plate, make_model, chassis_number, colour, year, mileage)
        )
        conn.commit()
        flash('Vehicle registered successfully!', 'success')
    except Exception:
        conn.rollback()
        flash('This license plate already exists in the system.', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('customer.dashboard'))

# 6. Book Service GET Route
@customer_bp.route('/customer/book-service', methods=['GET'])
def book_service_page():
    if 'user_id' not in session or session.get('role') != 'Customer':
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    selected_vehicle_id = request.args.get('vehicle_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles WHERE customer_id = %s", (user_id,))
    vehicles = cursor.fetchall()
    conn.close()

    return render_template('customer/book_service.html', vehicles=vehicles, selected_vehicle_id=selected_vehicle_id)

# 7. Book Service POST Route (Updates current mileage on vehicle)
@customer_bp.route('/customer/add-booking', methods=['POST'])
def add_booking():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    customer_id = session['user_id']
    vehicle_id = request.form.get('vehicle_id')
    booking_date = request.form.get('booking_date')
    time_slot = request.form.get('time_slot')
    service_type = request.form.get('service_type')
    current_mileage = request.form.get('current_mileage', type=int)

    if current_mileage is None or current_mileage < 0:
        flash('Please enter a valid current mileage (km).', 'danger')
        return redirect(url_for('customer.book_service_page', vehicle_id=vehicle_id))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO appointments (customer_id, vehicle_id, booking_date, time_slot, service_type, status) 
               VALUES (%s, %s, %s, %s, %s, 'Pending')""",
            (customer_id, vehicle_id, booking_date, time_slot, service_type)
        )
        cursor.execute(
            """UPDATE vehicles
               SET mileage = %s
               WHERE vehicle_id = %s AND customer_id = %s""",
            (current_mileage, vehicle_id, customer_id)
        )
        conn.commit()
        flash('Service Appointment booked and current mileage updated!', 'success')
    except Exception:
        conn.rollback()
        flash('An error occurred while booking the appointment.', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('customer.bookings_page'))

# 8. Bills List Page Route (නව Route එක)
@customer_bp.route('/customer/bills')
def bills_page():
    if 'user_id' not in session or session.get('role') != 'Customer':
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT i.*, a.booking_date, a.service_type, v.license_plate, v.make_model
        FROM invoices i
        JOIN appointments a ON i.appointment_id = a.appointment_id
        JOIN vehicles v ON a.vehicle_id = v.vehicle_id
        WHERE i.customer_id = %s
        ORDER BY i.created_at DESC
    """, (user_id,))
    bills = cursor.fetchall()
    conn.close()

    return render_template('customer/bills.html', bills=bills)

# 9. View / Print Invoice Route (නව Route එක)
@customer_bp.route('/customer/bill/<int:invoice_id>')
def view_bill(invoice_id):
    if 'user_id' not in session or session.get('role') != 'Customer':
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT i.*, a.booking_date, a.service_type, a.time_slot,
               v.license_plate, v.make_model, v.chassis_number, v.colour,
               u.full_name, u.email, u.phone
        FROM invoices i
        JOIN appointments a ON i.appointment_id = a.appointment_id
        JOIN vehicles v ON a.vehicle_id = v.vehicle_id
        JOIN users u ON i.customer_id = u.user_id
        WHERE i.invoice_id = %s AND i.customer_id = %s
    """, (invoice_id, user_id))
    bill = cursor.fetchone()
    conn.close()

    if not bill:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('customer.bills_page'))

    return render_template('customer/view_bill.html', bill=bill)

# 10. Feedback Route
@customer_bp.route('/customer/feedback', methods=['GET', 'POST'])
def feedback_page():
    if 'user_id' not in session or session.get('role') != 'Customer':
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    if request.method == 'POST':
        rating = request.form.get('rating')
        comments = request.form.get('comments')

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO feedback (customer_id, rating, comments) VALUES (%s, %s, %s)",
                (user_id, rating, comments)
            )
            conn.commit()
            flash('Your feedback has been submitted successfully!', 'success')
        except Exception:
            conn.rollback()
            flash('An error occurred while submitting the feedback.', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('customer.feedback_page'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback WHERE customer_id = %s ORDER BY created_at DESC", (user_id,))
    user_feedbacks = cursor.fetchall()
    conn.close()

    return render_template('customer/feedback.html', user_feedbacks=user_feedbacks)

# 11. Settings Route
@customer_bp.route('/customer/settings', methods=['GET', 'POST'])
def settings_page():
    if 'user_id' not in session or session.get('role') != 'Customer':
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        new_password = request.form.get('new_password')

        try:
            if new_password and new_password.strip():
                hashed_pw = generate_password_hash(new_password)
                cursor.execute(
                    "UPDATE users SET full_name = %s, email = %s, phone = %s, password = %s WHERE user_id = %s",
                    (full_name, email, phone, hashed_pw, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET full_name = %s, email = %s, phone = %s WHERE user_id = %s",
                    (full_name, email, phone, user_id)
                )

            conn.commit()
            session['full_name'] = full_name
            flash('Your account information has been updated successfully!', 'success')
        except Exception:
            conn.rollback()
            flash('An error occurred while updating the information.', 'danger')
        finally:
            conn.close()

        return redirect(url_for('customer.settings_page'))

    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user_info = cursor.fetchone()
    conn.close()

    return render_template('customer/settings.html', user_info=user_info)