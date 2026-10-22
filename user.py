from collections import defaultdict
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from models import db, CollectionPoint, Submission, Transaction, WasteCategory
from services.rewards import MAX_WEIGHT_G

bp = Blueprint("user", __name__)


@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@bp.route("/api/stats")
@login_required
def stats():
    """Own data for users; platform-wide data for collectors/admins."""
    sq = Submission.query
    tq = Transaction.query.filter(Transaction.amount > 0)
    if current_user.role == "user":
        sq = sq.filter_by(user_id=current_user.id)
        tq = tq.filter_by(user_id=current_user.id)
    subs, txs = sq.all(), tq.order_by(Transaction.created_at).all()

    by_day = defaultdict(int)
    for t in txs:
        by_day[t.created_at.strftime("%d %b")] += t.amount
    by_cat = defaultdict(float)
    for s in subs:
        if s.status == "approved":
            by_cat[s.category.name] += s.verified_weight_g / 1000
    status = {k: sum(1 for s in subs if s.status == k) for k in ("pending", "approved", "rejected")}
    return jsonify(
        scope="mine" if current_user.role == "user" else "all",
        balance=current_user.balance,
        total_coins=sum(t.amount for t in txs),
        total_kg=round(sum(by_cat.values()), 2),
        submissions=len(subs),
        coins_by_day={"labels": list(by_day), "values": list(by_day.values())},
        kg_by_category={"labels": list(by_cat), "values": [round(v, 2) for v in by_cat.values()]},
        status=status,
    )


@bp.route("/submit", methods=["GET", "POST"])
@login_required
def submit():
    categories = WasteCategory.query.filter_by(is_active=True).all()
    points = CollectionPoint.query.filter_by(is_active=True).all()
    if request.method == "POST":
        try:
            weight_g = int(round(float(request.form["weight_kg"]) * 1000))
            category = db.session.get(WasteCategory, int(request.form["category_id"]))
            point = db.session.get(CollectionPoint, int(request.form["point_id"]))
        except (KeyError, ValueError):
            flash("Please fill in every field with valid values.", "error")
            return render_template("submit.html", categories=categories, points=points)
        if not (0 < weight_g <= MAX_WEIGHT_G):
            flash("Weight must be above 0 and at most 100 kg.", "error")
        elif not category or not category.is_active or not point or not point.is_active:
            flash("Choose an active category and collection point.", "error")
        else:
            db.session.add(Submission(
                user_id=current_user.id, category_id=category.id, point_id=point.id,
                claimed_weight_g=weight_g, note=request.form.get("note", "").strip()[:200]))
            db.session.commit()
            flash("Submitted! A collector will verify it soon.", "success")
            return redirect(url_for("user.wallet"))
    return render_template("submit.html", categories=categories, points=points)


@bp.route("/wallet")
@login_required
def wallet():
    txs = Transaction.query.filter_by(user_id=current_user.id) \
        .order_by(Transaction.created_at.desc()).all()
    subs = Submission.query.filter_by(user_id=current_user.id) \
        .order_by(Submission.created_at.desc()).all()
    return render_template("wallet.html", txs=txs, subs=subs)
