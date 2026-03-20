import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from admin_portal.utils import admin_required
from shared import db

admin_pricing_bp = Blueprint('admin_pricing', __name__)

@admin_pricing_bp.route('/')
@admin_required
def pricing_list():
    zones = db.find('zones')
    zones.sort(key=lambda z: z.get('name', ''))
    return render_template('admin/pricing.html', zones=zones)

@admin_pricing_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_zone():
    if request.method == 'POST':
        f = request.form
        name = f.get('name','').strip()
        if not name:
            flash('Zone name is required.', 'danger')
            return render_template('admin/pricing_form.html', zone=None, action='Add')

        zone = db.insert_one('zones', {
            'name':             name,
            'state':            f.get('state','').strip(),
            'district':         f.get('district','').strip(),
            'base_fare':        float(f.get('base_fare', 30)),
            'per_km_rate':      float(f.get('per_km_rate', 12)),
            'per_hour_rate':    float(f.get('per_hour_rate', 80)),
            'minimum_fare':     float(f.get('minimum_fare', 50)),
            'night_surcharge':  float(f.get('night_surcharge', 1.3)),
            'peak_multiplier':  float(f.get('peak_multiplier', 1.5)),
            'cancellation_pct': float(f.get('cancellation_pct', 10)),
            'emergency_multiplier': float(f.get('emergency_multiplier', 1.5)),
            'active':           True,
        })
        flash(f'Zone "{name}" created.', 'success')
        return redirect(url_for('admin_pricing.pricing_list'))

    return render_template('admin/pricing_form.html', zone=None, action='Add')

@admin_pricing_bp.route('/<zone_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_zone(zone_id):
    zone = db.find_one('zones', {'_id': zone_id})
    if not zone:
        flash('Zone not found.', 'danger')
        return redirect(url_for('admin_pricing.pricing_list'))

    if request.method == 'POST':
        f = request.form
        db.update_one('zones', {'_id': zone_id}, {
            'name':             f.get('name','').strip(),
            'state':            f.get('state','').strip(),
            'district':         f.get('district','').strip(),
            'base_fare':        float(f.get('base_fare', 30)),
            'per_km_rate':      float(f.get('per_km_rate', 12)),
            'per_hour_rate':    float(f.get('per_hour_rate', 80)),
            'minimum_fare':     float(f.get('minimum_fare', 50)),
            'night_surcharge':  float(f.get('night_surcharge', 1.3)),
            'peak_multiplier':  float(f.get('peak_multiplier', 1.5)),
            'cancellation_pct': float(f.get('cancellation_pct', 10)),
            'emergency_multiplier': float(f.get('emergency_multiplier', 1.5)),
        })
        flash(f'Zone "{f.get("name")}" updated. Changes live immediately.', 'success')
        return redirect(url_for('admin_pricing.pricing_list'))

    return render_template('admin/pricing_form.html', zone=zone, action='Edit')

@admin_pricing_bp.route('/<zone_id>/toggle', methods=['POST'])
@admin_required
def toggle_zone(zone_id):
    zone = db.find_one('zones', {'_id': zone_id})
    if not zone:
        return jsonify({'error': 'Not found'}), 404
    new_active = not zone.get('active', True)
    db.update_one('zones', {'_id': zone_id}, {'active': new_active})
    return jsonify({'success': True, 'active': new_active})

@admin_pricing_bp.route('/<zone_id>/delete', methods=['POST'])
@admin_required
def delete_zone(zone_id):
    db.delete_one('zones', {'_id': zone_id})
    flash('Zone deleted.', 'warning')
    return redirect(url_for('admin_pricing.pricing_list'))

@admin_pricing_bp.route('/api/preview')
@admin_required
def fare_preview():
    """Live fare calculator preview."""
    zone_id  = request.args.get('zone_id','')
    hours    = float(request.args.get('hours', 1))
    km       = float(request.args.get('km', 0))
    is_night = request.args.get('night','') == '1'
    is_peak  = request.args.get('peak','')  == '1'
    is_emerg = request.args.get('emergency','') == '1'

    zone = db.find_one('zones', {'_id': zone_id})
    if not zone:
        return jsonify({'error': 'Zone not found'}), 404

    base     = float(zone.get('base_fare', 30))
    per_km   = float(zone.get('per_km_rate', 12))
    per_hour = float(zone.get('per_hour_rate', 80))
    min_fare = float(zone.get('minimum_fare', 50))
    night_x  = float(zone.get('night_surcharge', 1.3))
    peak_x   = float(zone.get('peak_multiplier', 1.5))
    emerg_x  = float(zone.get('emergency_multiplier', 1.5))

    fare = base + (per_km * km) + (per_hour * hours)
    multiplier = 1.0
    if is_night:  multiplier *= night_x
    if is_peak:   multiplier *= peak_x
    if is_emerg:  multiplier *= emerg_x
    fare = max(fare * multiplier, min_fare)

    return jsonify({
        'base':       base,
        'km_cost':    round(per_km * km, 2),
        'hour_cost':  round(per_hour * hours, 2),
        'multiplier': round(multiplier, 2),
        'total':      round(fare, 2),
    })
