from flask import Blueprint

routines_bp = Blueprint("routines", __name__)

from app.routines import routes
