import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify, session)
from functools import wraps
from shared import db

driver_rides_bp = Blueprint('driver_rides', __name__)

def driver_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'driver' or not session.get('user_id'):
            return redirect(url_for('driver_auth.login'))
        return f(*args, **kwargs)
    return decorated

def get_driver():
    uid = session.get('user_id', '')
    if not uid:
        return None
    return db.find_one('drivers', {'_id': uid})

@driver_rides_bp.route('/')
@driver_required
def my_rides():
    driver = get_driver()
    if not driver:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('driver_auth.login'))
    bookings = db.find('bookings', {'driver_id': driver['_id']})
    bookings.sort(key=lambda b: b.get('created_at', ''), reverse=True)
    return render_template('driver/my_rides.html', driver=driver, bookings=bookings)

@driver_rides_bp.route('/<booking_id>')
@driver_required
def ride_detail(booking_id):
    driver = get_driver()
    if not driver:
        session.clear()
        return redirect(url_for('driver_auth.login'))
    booking = db.find_one('bookings', {'_id': booking_id})
    if not booking:
        flash('Ride not found.', 'danger')
        return redirect(url_for('driver_rides.my_rides'))
    customer = db.find_one('users', {'_id': booking.get('customer_id', '')}) if booking.get('customer_id') else None
    return render_template('driver/ride_detail.html',
                           driver=driver, booking=booking, customer=customer)

@driver_rides_bp.route('/<booking_id>/status', methods=['POST'])
@driver_required
def update_status(booking_id):
    driver  = get_driver()
    if not driver:
        return jsonify({'success': False, 'error': 'Session expired'}), 401
    booking = db.find_one('bookings', {'_id': booking_id})
    if not booking or booking.get('driver_id') != driver['_id']:
        return jsonify({'success': False, 'error': 'Not authorized'}), 403

    data       = request.get_json() or {}
    new_status = data.get('status', '')
    if new_status not in ('in_progress', 'completed'):
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

    db.update_one('bookings', {'_id': booking_id}, {'status': new_status})

    if new_status == 'completed':
        earn = float(booking.get('fare', 0)) * 0.80
        db.update_one('drivers', {'_id': driver['_id']}, {
            'total_rides':    (driver.get('total_rides', 0) or 0) + 1,
            'total_earnings': round((driver.get('total_earnings', 0.0) or 0.0) + earn, 2),
            'wallet':         round((driver.get('wallet', 0.0) or 0.0) + earn, 2),
        })

    return jsonify({'success': True, 'status': new_status})

@driver_rides_bp.route('/api/active')
@driver_required
def active_ride_api():
    driver = get_driver()
    if not driver:
        return jsonify({'active': None})
    booking = db.find_one('bookings', {'driver_id': driver['_id'], 'status': 'in_progress'})
    if not booking:
        return jsonify({'active': None})
    customer = db.find_one('users', {'_id': booking.get('customer_id', '')}) if booking.get('customer_id') else None
    return jsonify({'active': {
        '_id':     booking['_id'],
        'pickup':  booking.get('pickup_address', ''),
        'dropoff': booking.get('dropoff_address', ''),
        'fare':    booking.get('fare', 0),
        'hours':   booking.get('hours', 1),
        'customer':customer.get('name', '') if customer else '',
        'phone':   customer.get('phone', '') if customer else '',
    }})

@driver_rides_bp.route('/api/booking-locations/<booking_id>')
@driver_required
def booking_locations_api(booking_id):
    """Returns pickup, dropoff, and customer coords for driver map."""
    driver  = get_driver()
    if not driver:
        return jsonify({'error': 'Session expired'}), 401
    booking = db.find_one('bookings', {'_id': booking_id})
    if not booking or booking.get('driver_id') != driver['_id']:
        return jsonify({'error': 'Not authorized'}), 403

    return jsonify({
        'pickup': {
            'lat':     booking.get('pickup_lat', 0),
            'lng':     booking.get('pickup_lng', 0),
            'address': booking.get('pickup_address', ''),
        },
        'dropoff': {
            'lat':     booking.get('dropoff_lat', 0),
            'lng':     booking.get('dropoff_lng', 0),
            'address': booking.get('dropoff_address', ''),
        },
        'distance_km': booking.get('distance_km', 0),
        'fare':        booking.get('fare', 0),
        'customer':    booking.get('customer_name', ''),
        'status':      booking.get('status', ''),
    })
