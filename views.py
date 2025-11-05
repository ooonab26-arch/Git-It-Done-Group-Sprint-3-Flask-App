from flask import Flask, Blueprint, render_template

main_blueprint = Blueprint('homepage', __name__)

@main_blueprint.route('/')
def dashboard():
    return render_template('dashboard.html')
