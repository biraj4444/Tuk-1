import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, jsonify, send_from_directory
from shared import db
from shared.auth import current_user
from shared.config import Config

home_bp = Blueprint('home', __name__)

# ── PWA: serve manifest and service worker from root ──────────────────────────
@home_bp.route('/manifest.json')
def manifest():
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), '..', 'static'),
        'manifest.json',
        mimetype='application/manifest+json'
    )

@home_bp.route('/sw.js')
def service_worker():
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), '..', 'static'),
        'sw.js',
        mimetype='application/javascript'
    )
# ──────────────────────────────────────────────────────────────────────────────

@home_bp.route('/')
def index():
    user           = current_user()
    total_drivers  = db.count('drivers', {'status': 'online'})
    total_bookings = db.count('bookings')
    zones          = db.find('zones')
    return render_template('customer/index.html',
                           user=user,
                           total_drivers=total_drivers,
                           total_bookings=total_bookings,
                           zones=zones,
                           maptiler_key=Config.MAPTILER_KEY_SAT,
                           maptiler_key_sat=Config.MAPTILER_KEY_SAT,
                           maptiler_key_street=Config.MAPTILER_KEY_STREET,
                           ipinfo_token=Config.IPINFO_TOKEN)

@home_bp.route('/api/drivers/available')
def available_drivers():
    drivers = db.find('drivers', {'status': 'online'})
    safe = [{
        '_id':    d['_id'],
        'name':   d.get('name', ''),
        'rating': d.get('rating', 5.0),
        'lat':    d.get('lat', 0),
        'lng':    d.get('lng', 0),
        'vehicle':d.get('vehicle_number', ''),
        'avatar': d.get('avatar', ''),
    } for d in drivers]
    return jsonify({'drivers': safe, 'count': len(safe)})
