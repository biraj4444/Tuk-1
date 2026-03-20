import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from shared import db
from shared.config import Config
from shared.auth import login_required, current_user

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_booking():
    zones   = db.find('zones')
    drivers = db.find('drivers', {'status': 'online'})

    if request.method == 'POST':
        user        = current_user()
        data        = request.form
        pickup      = data.get('pickup_address', '').strip()
        dropoff     = data.get('dropoff_address', '').strip()
        pickup_lat  = float(data.get('pickup_lat',  0) or 0)
        pickup_lng  = float(data.get('pickup_lng',  0) or 0)
        dropoff_lat = float(data.get('dropoff_lat', 0) or 0)
        dropoff_lng = float(data.get('dropoff_lng', 0) or 0)
        zone_id     = data.get('zone_id', '').strip()
        book_type   = data.get('booking_type', 'now')
        hours       = float(data.get('hours', 1) or 1)
        date_time   = data.get('scheduled_datetime', '')
        driver_id   = data.get('driver_id', '')
        notes       = data.get('notes', '')
        distance_km = float(data.get('distance_km', 0) or 0)

        if not pickup or not zone_id:
            flash('Pickup address and zone are required.', 'danger')
            return render_template('customer/booking_new.html', zones=zones, drivers=drivers,
                           maptiler_key=Config.MAPTILER_KEY)

        zone = db.find_one('zones', {'_id': zone_id})
        fare = 50.0
        if zone:
            base     = float(zone.get('base_fare', 30))
            per_km   = float(zone.get('per_km_rate', 12))
            per_hour = float(zone.get('per_hour_rate', 80))
            min_fare = float(zone.get('minimum_fare', 50))
            fare = max(base + (per_km * distance_km) + (per_hour * hours), min_fare)

        booking = db.insert_one('bookings', {
            'customer_id':        user['_id'],
            'customer_name':      user['name'],
            'customer_email':     user['email'],
            'pickup_address':     pickup,
            'dropoff_address':    dropoff,
            'pickup_lat':         pickup_lat,
            'pickup_lng':         pickup_lng,
            'dropoff_lat':        dropoff_lat,
            'dropoff_lng':        dropoff_lng,
            'distance_km':        round(distance_km, 2),
            'zone_id':            zone_id,
            'booking_type':       book_type,
            'hours':              hours,
            'scheduled_datetime': date_time,
            'driver_id':          driver_id,
            'notes':              notes,
            'fare':               round(fare, 2),
            'status':             'pending',
            'payment_status':     'locked',   # locked until driver accepts
            'payment_locked':     True,
        })

        flash('Ride booked! Waiting for a driver to accept your request.', 'success')
        return redirect(url_for('booking.booking_detail', booking_id=booking['_id']))

    return render_template('customer/booking_new.html',
                           zones=zones, drivers=drivers,
                           pickup=request.args.get('pickup', ''),
                           dropoff=request.args.get('dropoff', ''),
                           prefill_driver=request.args.get('driver_id', ''),
                           maptiler_key=Config.MAPTILER_KEY)

@booking_bp.route('/my')
@login_required
def my_bookings():
    user     = current_user()
    bookings = db.find('bookings', {'customer_id': user['_id']})
    bookings.sort(key=lambda b: b.get('created_at', ''), reverse=True)
    return render_template('customer/my_bookings.html', bookings=bookings)

@booking_bp.route('/<booking_id>')
@login_required
def booking_detail(booking_id):
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id})
    if not booking or booking.get('customer_id') != user['_id']:
        flash('Booking not found.', 'danger')
        return redirect(url_for('booking.my_bookings'))
    driver  = db.find_one('drivers', {'_id': booking.get('driver_id', '')}) if booking.get('driver_id') else None
    payment = db.find_one('payments', {'booking_id': booking_id})
    return render_template('customer/booking_detail.html',
                           booking=booking, driver=driver, payment=payment)

@booking_bp.route('/<booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        return jsonify({'error': 'Not found'}), 404
    if booking['status'] not in ('pending', 'confirmed'):
        return jsonify({'error': 'Cannot cancel'}), 400
    db.update_one('bookings', {'_id': booking_id}, {'status': 'cancelled'})
    return jsonify({'success': True})

@booking_bp.route('/api/status/<booking_id>')
@login_required
def booking_status_api(booking_id):
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        return jsonify({'error': 'Not found'}), 404

    driver_info = None
    if booking.get('driver_id'):
        d = db.find_one('drivers', {'_id': booking['driver_id']})
        if d:
            driver_info = {
                'name':    d.get('name', ''),
                'phone':   d.get('phone', ''),
                'vehicle': d.get('vehicle_number', ''),
                'rating':  d.get('rating', 5.0),
                'lat':     d.get('lat', 0),
                'lng':     d.get('lng', 0),
                'avatar':  d.get('avatar', ''),
            }

    return jsonify({
        'status':         booking['status'],
        'payment_locked': booking.get('payment_locked', True),
        'payment_status': booking.get('payment_status', 'locked'),
        'driver':         driver_info,
        'fare':           booking.get('fare', 0),
    })

@booking_bp.route('/api/fare-estimate')
def fare_estimate_api():
    zone_id = request.args.get('zone_id', '')
    hours   = float(request.args.get('hours', 1) or 1)
    km      = float(request.args.get('km', 0) or 0)
    zone    = db.find_one('zones', {'_id': zone_id})
    if not zone:
        return jsonify({'error': 'Zone not found'}), 404
    base     = float(zone.get('base_fare', 30))
    per_km   = float(zone.get('per_km_rate', 12))
    per_hour = float(zone.get('per_hour_rate', 80))
    min_fare = float(zone.get('minimum_fare', 50))
    total    = max(base + (per_km * km) + (per_hour * hours), min_fare)
    return jsonify({
        'estimate': round(total, 2),
        'base': base, 'km_cost': round(per_km*km,2),
        'hr_cost': round(per_hour*hours,2), 'minimum': min_fare
    })

@booking_bp.route('/api/driver-location/<booking_id>')
@login_required
def driver_location_api(booking_id):
    """Real-time driver GPS for customer map — polls every 5s."""
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        return jsonify({'error': 'Not found'}), 404
    if not booking.get('driver_id'):
        return jsonify({'driver': None})

    driver = db.find_one('drivers', {'_id': booking['driver_id']})
    if not driver:
        return jsonify({'driver': None})

    return jsonify({
        'driver': {
            'lat':    driver.get('lat', 0),
            'lng':    driver.get('lng', 0),
            'name':   driver.get('name', ''),
            'rating': driver.get('rating', 5.0),
            'vehicle':driver.get('vehicle_number', ''),
        },
        'booking_status': booking.get('status', ''),
        'payment_locked': booking.get('payment_locked', True),
    })
