import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, jsonify
from admin_portal.utils import admin_required
from shared import db

admin_payments_bp = Blueprint('admin_payments', __name__)

@admin_payments_bp.route('/')
@admin_required
def payments_list():
    payments = db.find('payments')
    payments.sort(key=lambda p: p.get('created_at',''), reverse=True)
    total_revenue  = sum(float(p.get('amount',0)) for p in payments if p.get('status') not in ('payout',))
    platform_cut   = total_revenue * 0.20
    total_payouts  = sum(float(p.get('amount',0)) for p in payments if p.get('status') == 'payout')
    return render_template('admin/payments.html',
                           payments=payments,
                           total_revenue=total_revenue,
                           platform_cut=platform_cut,
                           total_payouts=total_payouts)
