from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from db import get_db_connection

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')


def is_owner():
    role = (session.get('role') or '').strip().lower()
    return role in ('owner', 'admin')


@owner_bp.route('/dashboard')
def dashboard():
    if not session.get('user_id') or not is_owner():
        flash('මෙම පිටුවට පිවිසීමට Owner අවසර අවශ්‍ය වේ.', 'warning')
        return redirect(url_for('auth.login'))

    conn = None
    cursor = None

    total_revenue = 0.0
    paid_total = 0.0
    unpaid_total = 0.0
    completed_services = 0
    active_jobs = 0
    low_stock_items = 0
    low_stock_list = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Paid Revenue
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) AS paid_rev
            FROM invoices
            WHERE LOWER(payment_status) = 'paid'
        """)
        row = cursor.fetchone()
        if row:
            paid_total = float(row['paid_rev'] if isinstance(row, dict) else row[0] or 0)
            total_revenue = paid_total

        # 2. Unpaid / Pending Bills Total
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) AS unpaid_rev
            FROM invoices
            WHERE LOWER(payment_status) != 'paid'
        """)
        row = cursor.fetchone()
        if row:
            unpaid_total = float(row['unpaid_rev'] if isinstance(row, dict) else row[0] or 0)

        # 3. Completed Services
        cursor.execute("""
            SELECT COUNT(*) AS cnt
            FROM service_bookings
            WHERE LOWER(status) = 'completed'
        """)
        row = cursor.fetchone()
        if row:
            completed_services = int(row['cnt'] if isinstance(row, dict) else row[0] or 0)

        # 4. Active Jobs in Bay
        cursor.execute("""
            SELECT COUNT(*) AS cnt
            FROM service_bookings
            WHERE LOWER(status) IN ('confirmed', 'in-progress', 'in progress')
        """)
        row = cursor.fetchone()
        if row:
            active_jobs = int(row['cnt'] if isinstance(row, dict) else row[0] or 0)

        # 5. Low Stock Items (stock_qty <= 10)
        cursor.execute("""
            SELECT COUNT(*) AS cnt
            FROM spare_parts
            WHERE stock_qty <= 10
        """)
        row = cursor.fetchone()
        if row:
            low_stock_items = int(row['cnt'] if isinstance(row, dict) else row[0] or 0)

        cursor.execute("""
            SELECT part_id, part_name, stock_qty, unit_price
            FROM spare_parts
            WHERE stock_qty <= 10
            ORDER BY stock_qty ASC, part_name ASC
            LIMIT 5
        """)
        low_stock_list = cursor.fetchall() or []

    except Exception as e:
        flash(f'දත්ත ලබා ගැනීමේදී දෝෂයක් ඇති විය: {e}', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template(
        'owner/dashboard.html',
        total_revenue=total_revenue,
        paid_total=paid_total,
        unpaid_total=unpaid_total,
        completed_services=completed_services,
        active_jobs=active_jobs,
        low_stock_items=low_stock_items,
        low_stock_list=low_stock_list,
        user_name=session.get('full_name') or session.get('user_name') or 'Owner'
    )


@owner_bp.route('/owner-dashboard')
def owner_dashboard():
    return redirect(url_for('owner.dashboard'))


@owner_bp.route('/reports')
def financial_reports():
    if not session.get('user_id') or not is_owner():
        flash('මෙම පිටුවට පිවිසීමට Owner අවසර අවශ්‍ය වේ.', 'warning')
        return redirect(url_for('auth.login'))

    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()

    conn = None
    cursor = None

    invoices_data = []
    paid_total = 0.0
    unpaid_total = 0.0

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                i.invoice_id,
                i.appointment_id,
                i.labor_charge,
                i.parts_charge,
                i.total_amount,
                i.payment_status,
                i.created_at,
                u.full_name AS customer_name
            FROM invoices i
            LEFT JOIN users u ON i.customer_id = u.user_id
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND DATE(i.created_at) >= %s"
            params.append(start_date)
        if end_date:
            query += " AND DATE(i.created_at) <= %s"
            params.append(end_date)

        query += " ORDER BY i.created_at DESC"
        cursor.execute(query, tuple(params))
        invoices_data = cursor.fetchall() or []

        for inv in invoices_data:
            status = (inv['payment_status'] if isinstance(inv, dict) else inv[5] or '').lower()
            amt = float((inv['total_amount'] if isinstance(inv, dict) else inv[4]) or 0)
            if status == 'paid':
                paid_total += amt
            else:
                unpaid_total += amt

    except Exception as e:
        flash(f'වාර්තා සකස් කිරීමේදී දෝෂයක් ඇති විය: {e}', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template(
        'owner/reports.html',
        invoices=invoices_data,
        paid_total=paid_total,
        unpaid_total=unpaid_total,
        start_date=start_date,
        end_date=end_date
    )