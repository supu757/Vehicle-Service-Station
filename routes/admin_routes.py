from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

def is_admin():
    return 'user_id' in session and session.get('role') == 'Admin'

def is_officer():
    return 'user_id' in session and session.get('role') == 'Service Officer'


# --- 1. SERVICE OFFICER MODULE (Dashboard, Jobs, Invoices, Inventory, Services) ---
@admin_bp.route('/admin/dashboard')
def dashboard():
    if not is_officer():
        flash('මෙම පිටුවට ප්‍රවේශ වීමට Service Officer අවසර අවශ්‍ය වේ.', 'danger')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.*, u.full_name as customer_name, u.phone as customer_phone, 
               v.license_plate, v.make_model,
               j.job_card_id, j.inspection_notes, j.job_status, j.technician_id,
               tech.full_name as technician_name,
               COALESCE((SELECT SUM(jp.total_price) FROM job_parts jp WHERE jp.job_card_id = j.job_card_id), 0) AS calc_parts_total
        FROM appointments a
        JOIN users u ON a.customer_id = u.user_id
        JOIN vehicles v ON a.vehicle_id = v.vehicle_id
        LEFT JOIN job_cards j ON a.appointment_id = j.appointment_id
        LEFT JOIN users tech ON j.technician_id = tech.user_id
        ORDER BY a.booking_date DESC, a.appointment_id DESC
    """)
    appointments = cursor.fetchall()

    cursor.execute("SELECT * FROM job_parts ORDER BY part_id ASC")
    all_job_parts = cursor.fetchall()
    parts_by_job = {}
    for p in all_job_parts:
        j_id = str(p['job_card_id'])
        parts_by_job.setdefault(j_id, []).append({
            'part_name': p['part_name'],
            'quantity': p['quantity'],
            'unit_price': float(p['unit_price']),
            'total_price': float(p['total_price'])
        })

    cursor.execute("SELECT * FROM services ORDER BY service_name ASC")
    services = cursor.fetchall()

    cursor.execute("SELECT user_id, full_name FROM users WHERE LOWER(TRIM(role)) = 'technician' ORDER BY full_name ASC")
    technicians = cursor.fetchall()

    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) AS today_revenue 
        FROM invoices 
        WHERE payment_status = 'Paid' AND DATE(COALESCE(payment_date, created_at)) = CURDATE()
    """)
    rev_row = cursor.fetchone()
    today_revenue = float(rev_row['today_revenue']) if rev_row else 0.0

    pending_count = sum(1 for app in appointments if app.get('status') == 'Pending')
    in_progress_count = sum(1 for app in appointments if app.get('status') in ['In Progress', 'Inspection'])
    completed_count = sum(1 for app in appointments if app.get('status') == 'Completed')

    conn.close()

    return render_template(
        'admin/dashboard.html',
        appointments=appointments,
        parts_by_job=parts_by_job,
        services=services,
        technicians=technicians,
        today_revenue=today_revenue,
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        completed_count=completed_count
    )

@admin_bp.route('/admin/assign-tech/<int:appointment_id>', methods=['POST'])
def assign_tech(appointment_id):
    if not is_officer():
        return redirect(url_for('auth.login'))
    technician_id = request.form.get('technician_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT job_card_id FROM job_cards WHERE appointment_id = %s", (appointment_id,))
    existing_job = cursor.fetchone()
    if existing_job:
        cursor.execute("UPDATE job_cards SET technician_id = %s WHERE appointment_id = %s", (technician_id, appointment_id))
    else:
        cursor.execute("INSERT INTO job_cards (appointment_id, technician_id, inspection_notes, job_status) VALUES (%s, %s, %s, 'In Progress')", 
                       (appointment_id, technician_id, 'Technician assigned by Service Officer'))
    cursor.execute("UPDATE appointments SET status = 'In Progress' WHERE appointment_id = %s AND status = 'Pending'", (appointment_id,))
    conn.commit()
    conn.close()
    flash('Technician සාර්ථකව පත් කරන ලදී!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/create-job-card/<int:appointment_id>', methods=['POST'])
def create_job_card(appointment_id):
    if not is_officer():
        return redirect(url_for('auth.login'))
    technician_id = request.form.get('technician_id')
    inspection_notes = request.form.get('inspection_notes')
    job_status = request.form.get('job_status', 'In Progress')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT job_card_id FROM job_cards WHERE appointment_id = %s", (appointment_id,))
    existing_job = cursor.fetchone()
    if existing_job:
        cursor.execute("UPDATE job_cards SET technician_id = %s, inspection_notes = %s, job_status = %s WHERE appointment_id = %s", 
                       (technician_id if technician_id else None, inspection_notes, job_status, appointment_id))
    else:
        cursor.execute("INSERT INTO job_cards (appointment_id, technician_id, inspection_notes, job_status) VALUES (%s, %s, %s, %s)", 
                       (appointment_id, technician_id if technician_id else None, inspection_notes, job_status))
    cursor.execute("UPDATE appointments SET status = %s WHERE appointment_id = %s", (job_status, appointment_id))
    conn.commit()
    conn.close()
    flash('Job Card එක සාර්ථකව යාවත්කාලීන කරන ලදී!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/generate-bill/<int:appointment_id>', methods=['POST'])
def generate_bill(appointment_id):
    if not is_officer():
        return redirect(url_for('auth.login'))
    labor_charge = max(0.0, float(request.form.get('labor_charge', 0)))
    parts_charge = max(0.0, float(request.form.get('parts_charge', 0)))
    total_amount = labor_charge + parts_charge
    payment_status = request.form.get('payment_status', 'Paid')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT customer_id FROM appointments WHERE appointment_id = %s", (appointment_id,))
    app = cursor.fetchone()
    if app:
        customer_id = app['customer_id']
        cursor.execute("SELECT invoice_id FROM invoices WHERE appointment_id = %s", (appointment_id,))
        existing_inv = cursor.fetchone()
        if existing_inv:
            p_date = "NOW()" if payment_status == 'Paid' else "NULL"
            cursor.execute(f"""
                UPDATE invoices 
                SET labor_charge = %s, parts_charge = %s, total_amount = %s, payment_status = %s, payment_date = {p_date}
                WHERE appointment_id = %s
            """, (labor_charge, parts_charge, total_amount, payment_status, appointment_id))
        else:
            if payment_status == 'Paid':
                cursor.execute("""
                    INSERT INTO invoices (appointment_id, customer_id, labor_charge, parts_charge, total_amount, payment_status, payment_date)
                    VALUES (%s, %s, %s, %s, %s, 'Paid', NOW())
                """, (appointment_id, customer_id, labor_charge, parts_charge, total_amount))
            else:
                cursor.execute("""
                    INSERT INTO invoices (appointment_id, customer_id, labor_charge, parts_charge, total_amount, payment_status)
                    VALUES (%s, %s, %s, %s, %s, 'Unpaid')
                """, (appointment_id, customer_id, labor_charge, parts_charge, total_amount))
        cursor.execute("UPDATE appointments SET status = 'Completed' WHERE appointment_id = %s", (appointment_id,))
        cursor.execute("UPDATE job_cards SET job_status = 'Completed' WHERE appointment_id = %s", (appointment_id,))
        conn.commit()
        flash('අවසන් බිල්පත සාර්ථකව නිකුත් කරන ලදී!', 'success')
    conn.close()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/invoices')
def invoices_page():
    if not is_officer():
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, u.full_name AS customer_name, u.phone AS customer_phone,
               v.license_plate, v.make_model, a.service_type
        FROM invoices i
        JOIN users u ON i.customer_id = u.user_id
        JOIN appointments a ON i.appointment_id = a.appointment_id
        JOIN vehicles v ON a.vehicle_id = v.vehicle_id
        ORDER BY i.created_at DESC
    """)
    invoices = cursor.fetchall()
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) AS today_revenue FROM invoices WHERE payment_status = 'Paid' AND DATE(COALESCE(payment_date, created_at)) = CURDATE()")
    today_rev = float(cursor.fetchone()['today_revenue'])
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) AS total_revenue FROM invoices WHERE payment_status = 'Paid'")
    total_rev = float(cursor.fetchone()['total_revenue'])
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) AS unpaid_total FROM invoices WHERE payment_status = 'Unpaid'")
    unpaid_total = float(cursor.fetchone()['unpaid_total'])
    conn.close()
    return render_template('admin/invoices.html', invoices=invoices, today_revenue=today_rev, total_revenue=total_rev, unpaid_total=unpaid_total)

@admin_bp.route('/admin/mark-paid/<int:invoice_id>', methods=['POST'])
def mark_paid(invoice_id):
    if not is_officer():
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE invoices SET payment_status = 'Paid', payment_date = NOW() WHERE invoice_id = %s", (invoice_id,))
    conn.commit()
    conn.close()
    flash('ගෙවීම සාර්ථකව සටහන් කරන ලදී!', 'success')
    return redirect(url_for('admin.invoices_page'))

@admin_bp.route('/admin/feedback')
def feedback_page():
    if not is_officer():
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT f.*, u.full_name, u.email, u.phone FROM feedback f JOIN users u ON f.customer_id = u.user_id ORDER BY f.created_at DESC")
    feedbacks = cursor.fetchall()
    avg_rating = round(sum(f['rating'] for f in feedbacks) / len(feedbacks), 1) if feedbacks else 0.0
    conn.close()
    return render_template('admin/feedback.html', feedbacks=feedbacks, avg_rating=avg_rating)

@admin_bp.route('/admin/vehicles')
def vehicles_page():
    if not is_officer():
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT v.*, u.full_name AS owner_name, u.phone AS owner_phone, u.email AS owner_email FROM vehicles v JOIN users u ON v.customer_id = u.user_id ORDER BY v.vehicle_id DESC")
    vehicles = cursor.fetchall()
    conn.close()
    return render_template('admin/vehicles.html', vehicles=vehicles)


# --- 2. SERVICE OFFICER: INVENTORY & SERVICES MANAGEMENT ---
@admin_bp.route('/sys-admin/inventory')
def sys_inventory():
    if not is_officer():
        flash('මෙම පිටුවට ප්‍රවේශ වීමට Service Officer අවසර අවශ්‍ය වේ.', 'danger')
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT part_id, part_name, stock_qty, unit_price FROM spare_parts ORDER BY part_name ASC")
    parts = cursor.fetchall()
    conn.close()
    return render_template('admin/sys_inventory.html', parts=parts)

@admin_bp.route('/sys-admin/save-part', methods=['POST'])
def sys_save_part():
    if not is_officer():
        return redirect(url_for('auth.login'))
    part_id = request.form.get('part_id')
    part_name = request.form.get('part_name')
    stock_qty = int(request.form.get('stock_qty', 0))
    unit_price = float(request.form.get('unit_price', 0))

    conn = get_db_connection()
    cursor = conn.cursor()
    if part_id:
        cursor.execute("UPDATE spare_parts SET part_name = %s, stock_qty = %s, unit_price = %s WHERE part_id = %s",
                       (part_name, stock_qty, unit_price, part_id))
        flash('අමතර කොටස යාවත්කාලීන කරන ලදී!', 'success')
    else:
        cursor.execute("INSERT INTO spare_parts (part_name, stock_qty, unit_price) VALUES (%s, %s, %s)",
                       (part_name, stock_qty, unit_price))
        flash('නව අමතර කොටසක් සාර්ථකව එකතු කරන ලදී!', 'success')
    conn.commit()
    conn.close()
    return redirect(url_for('admin.sys_inventory'))

@admin_bp.route('/sys-admin/delete-part/<int:part_id>', methods=['POST'])
def sys_delete_part(part_id):
    if not is_officer():
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM spare_parts WHERE part_id = %s", (part_id,))
    conn.commit()
    conn.close()
    flash('අමතර කොටස ඉවත් කරන ලදී.', 'success')
    return redirect(url_for('admin.sys_inventory'))

@admin_bp.route('/sys-admin/services')
def sys_services():
    if not is_officer():
        flash('මෙම පිටුවට ප්‍රවේශ වීමට Service Officer අවසර අවශ්‍ය වේ.', 'danger')
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services ORDER BY service_name ASC")
    services = cursor.fetchall()
    conn.close()
    return render_template('admin/sys_services.html', services=services)

@admin_bp.route('/sys-admin/save-service', methods=['POST'])
def sys_save_service():
    if not is_officer():
        return redirect(url_for('auth.login'))
    service_id = request.form.get('service_id')
    service_name = request.form.get('service_name')
    base_price = float(request.form.get('base_price', 0))
    description = request.form.get('description')

    conn = get_db_connection()
    cursor = conn.cursor()
    if service_id:
        cursor.execute("SELECT service_id FROM services WHERE service_id = %s", (service_id,))
        # update logic if needed or standard insert/update
        cursor.execute("UPDATE services SET service_name = %s, base_price = %s, description = %s WHERE service_id = %s",
                       (service_name, base_price, description, service_id))
        flash('සේවා පැකේජය යාවත්කාලීන කරන ලදී!', 'success')
    else:
        cursor.execute("INSERT INTO services (service_name, base_price, description) VALUES (%s, %s, %s)",
                       (service_name, base_price, description))
        flash('නව සේවා පැකේජයක් සාර්ථකව එකතු කරන ලදී!', 'success')
    conn.commit()
    conn.close()
    return redirect(url_for('admin.sys_services'))

@admin_bp.route('/sys-admin/delete-service/<int:service_id>', methods=['POST'])
def sys_delete_service(service_id):
    if not is_officer():
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM services WHERE service_id = %s", (service_id,))
    conn.commit()
    conn.close()
    flash('සේවා පැකේජය ඉවත් කරන ලදී.', 'success')
    return redirect(url_for('admin.sys_services'))


# --- 3. SYSTEM ADMIN ONLY: USER MANAGEMENT ---
@admin_bp.route('/sys-admin/users')
def sys_users():
    if not is_admin():
        flash('මෙම පිටුවට ප්‍රවේශ වීමට Administrator අවසර අවශ්‍ය වේ.', 'danger')
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY user_id DESC")
    users = cursor.fetchall()
    conn.close()
    return render_template('admin/sys_users.html', users=users)

@admin_bp.route('/sys-admin/add-user', methods=['POST'])
def sys_add_user():
    if not is_admin():
        return redirect(url_for('auth.login'))
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    role = request.form.get('role')
    password = request.form.get('password')
    
    hashed_pwd = generate_password_hash(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (full_name, email, phone, role, password) VALUES (%s, %s, %s, %s, %s)",
                       (full_name, email, phone, role, hashed_pwd))
        conn.commit()
        flash('නව පරිශීලක ගිණුම සාර්ථකව සාදන ලදී!', 'success')
    except Exception as e:
        conn.rollback()
        flash('මෙම විද්‍යුත් තැපෑල (Email) දැනටමත් පවතී.', 'danger')
    conn.close()
    return redirect(url_for('admin.sys_users'))

@admin_bp.route('/sys-admin/delete-user/<int:user_id>', methods=['POST'])
def sys_delete_user(user_id):
    if not is_admin():
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()
    flash('පරිශීලක ගිණුම ඉවත් කරන ලදී.', 'success')
    return redirect(url_for('admin.sys_users'))