from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from models import db, Submission
from routes import role_required
from services.rewards import approve_submission, reject_submission

bp = Blueprint("collector", __name__)


@bp.route("/review")
@role_required("collector", "admin")
def review():
    pending = Submission.query.filter_by(status="pending").order_by(Submission.created_at).all()
    done = Submission.query.filter(Submission.status != "pending") \
        .order_by(Submission.reviewed_at.desc()).limit(10).all()
    return render_template("review.html", pending=pending, done=done)


@bp.route("/review/<int:sub_id>/approve", methods=["POST"])
@role_required("collector", "admin")
def approve(sub_id):
    sub = db.get_or_404(Submission, sub_id)
    try:
        grams = int(round(float(request.form["verified_kg"]) * 1000))
        coins = approve_submission(sub, current_user, grams)
        flash(f"Approved. {coins} EcoCoins credited to {sub.user.name}.", "success")
    except (KeyError, ValueError) as e:
        flash(str(e) or "Invalid weight.", "error")
    return redirect(url_for("collector.review"))


@bp.route("/review/<int:sub_id>/reject", methods=["POST"])
@role_required("collector", "admin")
def reject(sub_id):
    sub = db.get_or_404(Submission, sub_id)
    try:
        reject_submission(sub, current_user, request.form.get("reason", ""))
        flash("Submission rejected.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("collector.review"))
