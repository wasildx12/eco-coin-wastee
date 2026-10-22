from flask import Blueprint, flash, redirect, render_template, request, url_for
from models import db, CollectionPoint, WasteCategory
from routes import role_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@role_required("admin")
def home():
    return render_template("admin.html", points=CollectionPoint.query.all(),
                           categories=WasteCategory.query.all())


@bp.route("/point", methods=["POST"])
@role_required("admin")
def add_point():
    name, address = request.form.get("name", "").strip(), request.form.get("address", "").strip()
    if name and address:
        db.session.add(CollectionPoint(name=name, address=address))
        db.session.commit()
        flash("Collection point added.", "success")
    else:
        flash("Name and address are required.", "error")
    return redirect(url_for("admin.home"))


@bp.route("/point/<int:pid>/toggle", methods=["POST"])
@role_required("admin")
def toggle_point(pid):
    p = db.get_or_404(CollectionPoint, pid)
    p.is_active = not p.is_active
    db.session.commit()
    return redirect(url_for("admin.home"))


@bp.route("/category", methods=["POST"])
@role_required("admin")
def add_category():
    name = request.form.get("name", "").strip()
    try:
        rate = int(request.form["rate"])
        assert rate >= 0 and name
        assert not WasteCategory.query.filter_by(name=name).first()
        db.session.add(WasteCategory(name=name, coins_per_kg=rate))
        db.session.commit()
        flash("Category added.", "success")
    except (KeyError, ValueError, AssertionError):
        flash("Enter a unique name and a whole-number rate.", "error")
    return redirect(url_for("admin.home"))


@bp.route("/category/<int:cid>/update", methods=["POST"])
@role_required("admin")
def update_category(cid):
    c = db.get_or_404(WasteCategory, cid)
    try:
        rate = int(request.form["rate"])
        if rate < 0:
            raise ValueError
        c.coins_per_kg = rate
        c.is_active = "active" in request.form
        db.session.commit()
        flash("Category updated.", "success")
    except (KeyError, ValueError):
        flash("Rate must be a whole number of 0 or more.", "error")
    return redirect(url_for("admin.home"))
