from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection

technician_bp = Blueprint('technician', __name__)

def is_technician():
    return 'user_id' in session and session.get('role', '').strip().lower() == 'technician'

# 1. Technician Dashboard Route
@technician_bp.route('/technician/dashboard')
def dashboard():
    if not is_technician():
        flash('Please log in with a technician account to access this page.', 'danger')
        return redirect(url_for('auth.login'))

    tech_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # පැවරී ඇති Job Cards ලබාගැනීම
    cursor.execute("""
        SELECT j.job_card_id, j.appointment_id, j.inspection_notes, j.job_status, j.created_at,
               a.booking_date, a.time_slot, a.service_type,
               v.license_plate, v.make_model, v.year, v.colour, v.mileage,
               u.full_name AS customer_name, u.phone AS customer_phone
        FROM job_cards j
        JOIN appointments a ON j.appointment_id = a.appointment_id
        JOIN vehicles v ON a.vehicle_id = v.vehicle_id
        JOIN users u ON a.customer_id = u.user_id
        WHERE j.technician_id = %s
        ORDER BY 
            CASE j.job_status 
                WHEN 'In Progress' THEN 1 
                WHEN 'Inspection' THEN 2 
                WHEN 'Pending' THEN 3 
                ELSE 4 
            END,
            a.booking_date DESC
    """, (tech_id,))
    jobs = cursor.fetchall()

    # භාවිතා කළ Spare Parts ලබාගැනීම
    cursor.execute("""
        SELECT jp.* 
        FROM job_parts jp
        JOIN job_cards j ON jp.job_card_id = j.job_card_id
        WHERE j.technician_id = %s
        ORDER BY jp.part_id ASC
    """, (tech_id,))
    all_parts = cursor.fetchall()

    # Inventory එකේ ඇති Spare Parts සහ මිල ගණන් ලබාගැනීම
    cursor.execute("SELECT * FROM spare_parts ORDER BY part_name ASC")
    spare_parts = cursor.fetchall()

    parts_by_job = {}
    parts_total_by_job = {}
    for p in all_parts:
        j_id = p['job_card_id']
        parts_by_job.setdefault(j_id, []).append(p)
        parts_total_by_job[j_id] = parts_total_by_job.get(j_id, 0.0) + float(p['total_price'])

    total_jobs = len(jobs)
    pending_jobs = sum(1 for j in jobs if j.get('job_status') in ['Pending', 'Inspection'])
    in_progress_jobs = sum(1 for j in jobs if j.get('job_status') == 'In Progress')
    completed_jobs = sum(1 for j in jobs if j.get('job_status') == 'Completed')

    conn.close()

    return render_template(
        'technician/dashboard.html',
        jobs=jobs,
        spare_parts=spare_parts,
        parts_by_job=parts_by_job,
        parts_total_by_job=parts_total_by_job,
        total_jobs=total_jobs,
        pending_jobs=pending_jobs,
        in_progress_jobs=in_progress_jobs,
        completed_jobs=completed_jobs
    )

# 2. Update Job Status Route
@technician_bp.route('/technician/update-status/<int:job_card_id>', methods=['POST'])
def update_status(job_card_id):
    if not is_technician():
        return redirect(url_for('auth.login'))

    new_status = request.form.get('job_status')
    tech_notes = request.form.get('inspection_notes')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT appointment_id FROM job_cards WHERE job_card_id = %s AND technician_id = %s", (job_card_id, session['user_id']))
    job = cursor.fetchone()

    if job:
        if tech_notes is not None and tech_notes.strip() != '':
            cursor.execute(
                "UPDATE job_cards SET job_status = %s, inspection_notes = %s WHERE job_card_id = %s",
                (new_status, tech_notes, job_card_id)
            )
        else:
            cursor.execute(
                "UPDATE job_cards SET job_status = %s WHERE job_card_id = %s",
                (new_status, job_card_id)
            )

        cursor.execute(
            "UPDATE appointments SET status = %s WHERE appointment_id = %s",
            (new_status, job['appointment_id'])
        )
        conn.commit()
        flash(f'Job #{job_card_id} තත්ත්වය "{new_status}" ලෙස සාර්ථකව යාවත්කාලීන කරන ලදී!', 'success')

    conn.close()
    return redirect(url_for('technician.dashboard'))

# 3. Add Used Spare Parts from Inventory Table
@technician_bp.route('/technician/add-part/<int:job_card_id>', methods=['POST'])
def add_part(job_card_id):
    if not is_technician():
        return redirect(url_for('auth.login'))

    item_id = request.form.get('item_id')
    quantity = int(request.form.get('quantity', 1))

    if not item_id or quantity < 1:
        flash('Please select the spare part and quantity correctly.', 'danger')
        return redirect(url_for('technician.dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT job_card_id FROM job_cards WHERE job_card_id = %s AND technician_id = %s", (job_card_id, session['user_id']))
    job = cursor.fetchone()

    cursor.execute("SELECT * FROM spare_parts WHERE item_id = %s", (item_id,))
    part = cursor.fetchone()

    if job and part:
        part_name = part['part_name']
        unit_price = float(part['unit_price'])
        total_price = unit_price * quantity

        cursor.execute("""
            INSERT INTO job_parts (job_card_id, part_name, quantity, unit_price, total_price)
            VALUES (%s, %s, %s, %s, %s)
        """, (job_card_id, part_name, quantity, unit_price, total_price))

        # Stock ප්‍රමාණය අඩු කිරීම
        cursor.execute("""
            UPDATE spare_parts 
            SET stock_qty = GREATEST(stock_qty - %s, 0) 
            WHERE item_id = %s
        """, (quantity, item_id))

        conn.commit()
        flash(f'"{part_name}" (x{quantity}) Job Card එකට සාර්ථකව එකතු කරන ලදී!', 'success')

    conn.close()
    return redirect(url_for('technician.dashboard'))

# 4. Delete Used Part Route
@technician_bp.route('/technician/delete-part/<int:part_id>', methods=['POST'])
def delete_part(part_id):
    if not is_technician():
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE jp FROM job_parts jp
        JOIN job_cards j ON jp.job_card_id = j.job_card_id
        WHERE jp.part_id = %s AND j.technician_id = %s
    """, (part_id, session['user_id']))
    conn.commit()
    conn.close()

    flash('Spare part removed from the list successfully.', 'success')
    return redirect(url_for('technician.dashboard'))