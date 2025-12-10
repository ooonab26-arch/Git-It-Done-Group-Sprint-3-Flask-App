from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from models import db, User
import os
from dotenv import load_dotenv

# Blueprint
auth_blueprint = Blueprint('auth', __name__, url_prefix="/auth")

# Single global OAuth registry used everywhere
oauth = OAuth()
load_dotenv()

def init_oauth(app):
    """Attach OAuth to app and register the Google client."""
    oauth.init_app(app)

    print("DEBUG GOOGLE_CLIENT_ID =", app.config.get("GOOGLE_CLIENT_ID"))

    oauth.register(
        name="google",
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),

        # This URL gives Authlib *all* of Google's OpenID configuration,
        # including jwks_uri used to verify id_tokens.
        server_metadata_url=(
            "https://accounts.google.com/.well-known/openid-configuration"
        ),

        client_kwargs={
            "scope": "openid email profile",
            "prompt": "select_account",
        },
    )


# ==========================
# SIGNUP ROUTE
# ==========================
@auth_blueprint.route('/api/v1/auth/signup', methods=['GET', 'POST'])
def signUp():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        position = request.form.get('position') or "Staff"

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("User already exists. Please login.", "warning")
            return redirect(url_for('auth.signIn'))

        new_user = User(name=name, email=email, position=position)
        if password:
            new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Signup successful!", "success")
        return redirect(url_for('homepage.dashboard'))

    return render_template('sign-up.html')


# ==========================
# LOGIN ROUTE
# ==========================
@auth_blueprint.route('/api/v1/auth/signin', methods=['GET', 'POST'])
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
@auth_blueprint.route('/api/v1/auth/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for('auth.signIn'))


# ==========================
# GOOGLE SIGN-IN
# ==========================
@auth_blueprint.route('/google/login')
def google_login():
    """
    Redirect user to Google OAuth consent screen.
    Uses the GLOBAL oauth instance that was initialized in init_oauth(app).
    """
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)



@auth_blueprint.route('/google/callback')
def google_callback():
    """
    Handle the redirect back from Google and log the user in.
    """
    token = oauth.google.authorize_access_token()
    user_info = token.get("userinfo")
    if not user_info:
        user_info = oauth.google.parse_id_token(token)

    if not user_info:
        flash("Failed to get user info from Google.", "danger")
        return redirect(url_for('auth.signIn'))

    google_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name") or "Google User"

    if not email:
        flash("Google did not return an email address.", "danger")
        return redirect(url_for('auth.signIn'))

    # Try to find user by google_id first
    user = User.query.filter_by(google_id=google_id).first()

    # If not found, try by email
    if not user:
        user = User.query.filter_by(email=email).first()

    # If still not found, create new user
    if not user:
        user = User(
            name=name,
            email=email,
            position="Google User",
            google_id=google_id,
        )
        db.session.add(user)
    else:
        # Link Google ID to existing account if not already set
        if not getattr(user, "google_id", None):
            user.google_id = google_id

    db.session.commit()

    login_user(user)
    flash(f"Signed in as {name} via Google", "success")
    return redirect(url_for('homepage.dashboard'))
