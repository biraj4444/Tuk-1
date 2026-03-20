import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, jsonify, session, redirect, url_for, flash
from functools import wraps
from shared import db
from datetime import datetime

driver_earnings_bp = Blueprint('driver_earnings', __name__)

def driver_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'driver' or not session.get('user_id'):
            return redirect(url_for('driver_auth.login'))
        return f(*args, **kwargs)
    return decorated

def get_driver():
    uid = session.get('user_id', '')
    return db.find_one('drivers', {'_id': uid}) if uid else None

@driver_earnings_bp.route('/')
@driver_required
def earnings():
    driver = get_driver()
    if not driver:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('driver_auth.login'))

    bookings = db.find('bookings', {'driver_id': driver['_id'], 'status': 'completed'})
    bookings.sort(key=lambda b: b.get('created_at', ''), reverse=True)

    weekly = {}
    for b in bookings:
        day = b.get('created_at', '')[:10]
        if day:
            weekly[day] = weekly.get(day, 0) + float(b.get('fare', 0)) * 0.80
    weekly_sorted = sorted(weekly.items())[-7:]

    total_earn = sum(float(b.get('fare', 0)) * 0.80 for b in bookings)

    return render_template('driver/earnings.html',
                           driver=driver,
                           bookings=bookings,
                           weekly=weekly_sorted,
                           total_earn=total_earn)

@driver_earnings_bp.route('/api/summary')
@driver_required
def summary_api():
    driver = get_driver()
    if not driver:
        return jsonify({'error': 'Session expired'}), 401
    bookings  = db.find('bookings', {'driver_id': driver['_id'], 'status': 'completed'})
    today     = datetime.utcnow().strftime('%Y-%m-%d')
    today_r   = [b for b in bookings if b.get('created_at', '')[:10] == today]
    today_e   = sum(float(b.get('fare', 0)) * 0.80 for b in today_r)
    return jsonify({
        'today_rides':    len(today_r),
        'today_earnings': round(today_e, 2),
        'total_rides':    driver.get('total_rides', 0) or 0,
        'total_earnings': round(driver.get('total_earnings', 0.0) or 0.0, 2),
        'wallet':         round(driver.get('wallet', 0.0) or 0.0, 2),
        'rating':         driver.get('rating', 5.0) or 5.0,
    })
