from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()
        
        print("--- LOGIN DEBUG ---")
        print(f"Input Email: '{email}'")
        print(f"User Found from DB: {user}")
        
        password_matched = False
        if user:
            stored_pwd = user.get('password_hash') or user.get('password')
            print(f"Stored Password in DB: '{stored_pwd}'")
            
            if stored_pwd:
                # ඩේටාබේස් එකේ ඇත්තේ නිවැරදි Hash එකක් දැයි පරීක්ෂා කිරීම (උදා: pbkdf2 හෝ sha256 ආදී වශයෙන් `:` හෝ `$` අඩංගු වීම)
                if ':' in stored_pwd or '$' in stored_pwd:
                    try:
                        if check_password_hash(stored_pwd, password):
                            password_matched = True
                            print("Match result: Success via check_password_hash")
                    except Exception as e:
                        print(f"Hash check error: {e}")
                
                # නැතහොත් පරණ Plain Text එකක් නම් කෙලින්ම සංසන්දනය කිරීම
                if not password_matched and stored_pwd == password:
                    password_matched = True
                    print("Match result: Success via plain text comparison")
        
        print(f"Final password_matched: {password_matched}")
        print("-------------------")

        if user and password_matched:
            session['user_id'] = user['user_id']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            
            if user['role'] == 'Admin':
                return redirect(url_for('admin.sys_users'))
            elif user['role'] == 'Service Officer':
                return redirect(url_for('admin.dashboard'))
            elif user['role'] == 'Technician':
                return redirect(url_for('technician.dashboard'))
            elif user['role'] == 'Owner':
                return redirect(url_for('owner.owner_dashboard'))
            elif user['role'] == 'Customer':
                return redirect(url_for('customer.dashboard'))
            else:
                return redirect(url_for('auth.login'))
        else:
            flash('Invalid email or password!', 'danger')
            return render_template('auth/login.html')
            
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        role = request.form.get('role', 'Customer')

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (full_name, email, password_hash, phone, role) VALUES (%s, %s, %s, %s, %s)",
                (full_name, email, hashed_password, phone, role)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            conn.rollback()
            flash('This email is already registered.', 'danger')
        finally:
            conn.close()

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))