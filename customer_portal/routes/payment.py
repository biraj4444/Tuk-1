import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from shared import db
from shared.auth import login_required, current_user
from shared.payments import create_order, verify_payment, record_payment
from shared.config import Config

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/checkout/<booking_id>')
@login_required
def checkout(booking_id):
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('booking.my_bookings'))

    # ── PAYMENT LOCK CHECK ─────────────────────────────
    if booking.get('payment_locked', True):
        flash('Payment unlocks once a driver accepts your ride. Please wait.', 'info')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))
    # ───────────────────────────────────────────────────

    if booking.get('payment_status') == 'paid':
        flash('This booking is already paid.', 'info')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))

    order = create_order(
        amount_inr=booking['fare'],
        booking_id=booking_id,
        notes={'customer': user['name'], 'email': user['email']}
    )
    db.update_one('bookings', {'_id': booking_id}, {'razorpay_order_id': order['id']})

    return render_template('customer/checkout.html',
                           booking=booking, order=order,
                           rzp_key=Config.RAZORPAY_KEY_ID, user=user)

@payment_bp.route('/verify', methods=['POST'])
@login_required
def verify():
    data = request.get_json() or request.form
    razorpay_order_id   = data.get('razorpay_order_id', '')
    razorpay_payment_id = data.get('razorpay_payment_id', '')
    razorpay_signature  = data.get('razorpay_signature', '')
    booking_id          = data.get('booking_id', '')

    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    if verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        record_payment(booking_id, razorpay_order_id, razorpay_payment_id, booking['fare'])
        db.update_one('bookings', {'_id': booking_id}, {
            'payment_status':      'paid',
            'status':              'confirmed',
            'razorpay_payment_id': razorpay_payment_id,
        })
        # Award loyalty points
        points   = int(booking['fare'] / 10)
        customer = db.find_one('users', {'_id': user['_id']})
        db.update_one('users', {'_id': user['_id']}, {
            'loyalty_points': customer.get('loyalty_points', 0) + points
        })
        return jsonify({'success': True,
                        'redirect': url_for('booking.booking_detail', booking_id=booking_id)})

    return jsonify({'success': False, 'error': 'Payment verification failed'}), 400

@payment_bp.route('/success/<booking_id>')
@login_required
def success(booking_id):
    booking = db.find_one('bookings', {'_id': booking_id})
    return render_template('customer/payment_success.html', booking=booking)

@payment_bp.route('/failed/<booking_id>')
@login_required
def failed(booking_id):
    booking = db.find_one('bookings', {'_id': booking_id})
    return render_template('customer/payment_failed.html', booking=booking)
