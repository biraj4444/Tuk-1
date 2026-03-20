import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from admin_portal.utils import admin_required
from shared import db

admin_drivers_bp = Blueprint('admin_drivers', __name__)

@admin_drivers_bp.route('/')
@admin_required
def drivers_list():
    search   = request.args.get('q', '').strip().lower()
    approval = request.args.get('approval', '')
    status   = request.args.get('status', '')
    drivers  = db.find('drivers')

    if search:
        drivers = [d for d in drivers if
                   search in d.get('name','').lower() or
                   search in d.get('email','').lower() or
                   search in d.get('vehicle_number','').lower()]
    if approval:
        drivers = [d for d in drivers if d.get('approval') == approval]
    if status:
        drivers = [d for d in drivers if d.get('status') == status]

    drivers.sort(key=lambda d: d.get('created_at', ''), reverse=True)
    return render_template('admin/drivers.html',
                           drivers=drivers, search=search,
                           approval_filter=approval, status_filter=status)

@admin_drivers_bp.route('/<driver_id>')
@admin_required
def driver_detail(driver_id):
    driver = db.find_one('drivers', {'_id': driver_id})
    if not driver:
        flash('Driver not found.', 'danger')
        return redirect(url_for('admin_drivers.drivers_list'))
    rides  = db.find('bookings', {'driver_id': driver_id})
    rides.sort(key=lambda b: b.get('created_at', ''), reverse=True)
    return render_template('admin/driver_detail.html', driver=driver, rides=rides)

@admin_drivers_bp.route('/<driver_id>/approve', methods=['POST'])
@admin_required
def approve(driver_id):
    db.update_one('drivers', {'_id': driver_id},
                  {'approval': 'approved', 'status': 'offline'})
    flash('Driver approved. They can now go online.', 'success')
    return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))

@admin_drivers_bp.route('/<driver_id>/reject', methods=['POST'])
@admin_required
def reject(driver_id):
    db.update_one('drivers', {'_id': driver_id},
                  {'approval': 'rejected', 'status': 'offline'})
    flash('Driver application rejected.', 'warning')
    return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))

@admin_drivers_bp.route('/<driver_id>/suspend', methods=['POST'])
@admin_required
def suspend(driver_id):
    db.update_one('drivers', {'_id': driver_id},
                  {'status': 'suspended', 'approval': 'rejected'})
    flash('Driver suspended.', 'danger')
    return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))

@admin_drivers_bp.route('/<driver_id>/reinstate', methods=['POST'])
@admin_required
def reinstate(driver_id):
    db.update_one('drivers', {'_id': driver_id},
                  {'status': 'offline', 'approval': 'approved'})
    flash('Driver reinstated.', 'success')
    return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))

@admin_drivers_bp.route('/<driver_id>/payout', methods=['POST'])
@admin_required
def payout(driver_id):
    driver = db.find_one('drivers', {'_id': driver_id})
    if not driver:
        return jsonify({'error': 'Not found'}), 404
    amount = float(driver.get('wallet', 0))
    if amount <= 0:
        flash('No balance to pay out.', 'warning')
        return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))
    db.update_one('drivers', {'_id': driver_id}, {'wallet': 0.0})
    db.insert_one('payments', {
        'booking_id':          '',
        'razorpay_order_id':   '',
        'razorpay_payment_id': f'manual_payout_{driver_id[:8]}',
        'amount':              amount,
        'status':              'payout',
        'note':                f'Admin payout to driver {driver.get("name")}',
    })
    flash(f'Payout of ₹{amount:.2f} recorded for {driver["name"]}.', 'success')
    return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))

@admin_drivers_bp.route('/api/bulk-approve', methods=['POST'])
@admin_required
def bulk_approve():
    ids = request.get_json().get('ids', [])
    for did in ids:
        db.update_one('drivers', {'_id': did},
                      {'approval': 'approved', 'status': 'offline'})
    return jsonify({'success': True, 'count': len(ids)})
