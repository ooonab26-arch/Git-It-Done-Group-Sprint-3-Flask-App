from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

# Create the blueprint
auth_blueprint = Blueprint('auth', __name__)

# ==========================
# SIGNUP ROUTE
# ==========================
@auth_blueprint.route('/signup', methods=['GET', 'POST'])
def signUp():
    if request.method == 'POST':
        name = request.form.get('name')          # <-- grab the name
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("User already exists. Please login.", "warning")
            return redirect(url_for('auth.signin'))

        # Create new user
        new_user = User(name=name, email=email)   # <-- save name to the model
        new_user.set_password(password)           # Assumes you have set_password method

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Signup successful!", "success")
        return redirect(url_for('homepage.dashboard'))

    return render_template('sign-up.html')


# ==========================
# LOGIN ROUTE
# ==========================
@auth_blueprint.route('/signin', methods=['GET', 'POST'])
def signIn():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('homepage.dashboard'))
        else:
            flash("Invalid email or password", "danger")

    return render_template('sign-in.html')

# ==========================
# LOGOUT ROUTE
# ==========================
@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for('auth.sign-in'))
