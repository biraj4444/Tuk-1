import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify, session)
from functools import wraps
from shared import db
from datetime import datetime

driver_dash_bp = Blueprint('driver_dash', __name__)

# ── Auth guard ────────────────────────────────────────────────────────────────
def driver_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'driver' or not session.get('user_id'):
            flash('Please log in as a driver.', 'warning')
            return redirect(url_for('driver_auth.login'))
        return f(*args, **kwargs)
    return decorated

# ── Profile completeness guard ────────────────────────────────────────────────
def setup_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        uid = session.get('user_id', '')
        if not uid:
            return redirect(url_for('driver_auth.login'))
        driver = db.find_one('drivers', {'_id': uid})
        if not driver:
            session.clear()
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('driver_auth.login'))
        required = ['phone', 'vehicle_number', 'license_no']
        if not all(str(driver.get(field, '') or '').strip() for field in required):
            flash('Please complete your profile first.', 'warning')
            return redirect(url_for('driver_profile.setup'))
        return f(*args, **kwargs)
    return decorated

def get_driver():
    uid = session.get('user_id', '')
    if not uid:
        return None
    return db.find_one('drivers', {'_id': uid})

# ── Dashboard ─────────────────────────────────────────────────────────────────
@driver_dash_bp.route('/')
@driver_required
@setup_required
def dashboard():
    driver = get_driver()
    if not driver:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('driver_auth.login'))

    all_bookings = db.find('bookings', {'driver_id': driver['_id']})
    active = [b for b in all_bookings if b['status'] in ('confirmed', 'in_progress')]
    today  = datetime.utcnow().strftime('%Y-%m-%d')
    today_done = [b for b in all_bookings
                  if b['status'] == 'completed'
                  and b.get('created_at', '')[:10] == today]
    today_earn = sum(float(b.get('fare', 0)) * 0.80 for b in today_done)

    return render_template('driver/dashboard.html',
                           driver=driver,
                           active_rides=active,
                           today_rides=len(today_done),
                           today_earnings=today_earn)

# ── Toggle online/offline ─────────────────────────────────────────────────────
@driver_dash_bp.route('/toggle-status', methods=['POST'])
@driver_required
def toggle_status():
    driver = get_driver()
    if not driver:
        return jsonify({'success': False, 'error': 'Session expired'}), 401

    # FIX: proper toggle logic
    current = driver.get('status', 'offline')
    new_status = 'offline' if current == 'online' else 'online'

    if new_status == 'online' and driver.get('approval') != 'approved':
        return jsonify({
            'success': False,
            'error': 'Your account is pending admin approval. You cannot go online yet.'
        }), 403

    db.update_one('drivers', {'_id': driver['_id']}, {'status': new_status})
    return jsonify({'success': True, 'status': new_status})

# ── GPS location update ───────────────────────────────────────────────────────
@driver_dash_bp.route('/update-location', methods=['POST'])
@driver_required
def update_location():
    data = request.get_json() or {}
    uid  = session.get('user_id', '')
    if uid:
        db.update_one('drivers', {'_id': uid}, {
            'lat': float(data.get('lat', 0)),
            'lng': float(data.get('lng', 0)),
        })
    return jsonify({'success': True})

# ── Incoming requests polling ─────────────────────────────────────────────────
@driver_dash_bp.route('/api/requests')
@driver_required
def incoming_requests():
    driver = get_driver()
    if not driver:
        return jsonify({'requests': [], 'count': 0})

    # Driver must be online to receive requests
    if driver.get('status') != 'online':
        return jsonify({'requests': [], 'count': 0, 'offline': True})

    driver_id = driver['_id']

    # Get ALL pending bookings
    all_pending = db.find('bookings', {'status': 'pending'})

    # Show:
    # 1. Bookings with NO driver assigned (open to all online drivers)
    # 2. Bookings specifically pre-assigned to THIS driver
    available = [
        b for b in all_pending
        if (not b.get('driver_id') or b.get('driver_id') == '' or b.get('driver_id') == driver_id)
    ]

    result = [{
        '_id':       b['_id'],
        'pickup':    b.get('pickup_address', ''),
        'dropoff':   b.get('dropoff_address', ''),
        'fare':      b.get('fare', 0),
        'hours':     b.get('hours', 1),
        'type':      b.get('booking_type', 'now'),
        'customer':  b.get('customer_name', ''),
        'distance':  b.get('distance_km', 0),
        'scheduled': b.get('scheduled_datetime', ''),
        'assigned':  b.get('driver_id') == driver_id,  # true if pre-assigned to this driver
    } for b in available[:10]]

    return jsonify({'requests': result, 'count': len(result)})

# ── Accept ride → UNLOCK PAYMENT ─────────────────────────────────────────────
@driver_dash_bp.route('/accept/<booking_id>', methods=['POST'])
@driver_required
def accept_ride(booking_id):
    driver  = get_driver()
    if not driver:
        return jsonify({'success': False, 'error': 'Session expired'}), 401

    booking = db.find_one('bookings', {'_id': booking_id})
    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    # Allow if: no driver yet, OR pre-assigned to this driver
    existing_driver = booking.get('driver_id', '')
    if existing_driver and existing_driver != driver['_id']:
        return jsonify({'success': False, 'error': 'This ride was already taken by another driver.'}), 409

    # Must be pending
    if booking.get('status') != 'pending':
        return jsonify({'success': False, 'error': 'This booking is no longer available.'}), 409

    # Accept: assign driver + unlock payment
    db.update_one('bookings', {'_id': booking_id}, {
        'driver_id':      driver['_id'],
        'driver_name':    driver.get('name', ''),
        'driver_phone':   driver.get('phone', ''),
        'status':         'confirmed',
        'payment_locked': False,       # ← UNLOCK: customer can now pay
        'payment_status': 'unpaid',
    })

    return jsonify({
        'success':  True,
        'message':  'Ride accepted! Customer can now make payment.',
        'redirect': url_for('driver_rides.ride_detail', booking_id=booking_id)
    })

# ── Reject/skip ride ──────────────────────────────────────────────────────────
@driver_dash_bp.route('/reject/<booking_id>', methods=['POST'])
@driver_required
def reject_ride(booking_id):
    # Just skip — booking stays pending for other drivers
    return jsonify({'success': True})

# ── Debug endpoint: check what's in DB right now ──────────────────────────────
@driver_dash_bp.route('/api/debug')
@driver_required
def debug_info():
    driver = get_driver()
    if not driver:
        return jsonify({'error': 'no driver'}), 401
    pending = db.find('bookings', {'status': 'pending'})
    return jsonify({
        'driver_id':     driver['_id'],
        'driver_status': driver.get('status'),
        'approval':      driver.get('approval'),
        'pending_bookings': len(pending),
        'bookings_detail': [{
            '_id': b['_id'][:8],
            'driver_id': b.get('driver_id', '(none)'),
            'status': b.get('status'),
            'customer': b.get('customer_name',''),
        } for b in pending]
    })
