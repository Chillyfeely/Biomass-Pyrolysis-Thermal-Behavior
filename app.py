from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os, csv

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///biomass.db"
app.config["SECRET_KEY"] = os.urandom(24)
app.config["UPLOAD_FOLDER"] = "Uploaded"
db = SQLAlchemy(app)


class Mail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.String(200), nullable=True)
    serial_number = db.Column(db.String(200), nullable=True)
    sample_weight = db.Column(db.String(200), nullable=True)
    heat_interval = db.Column(db.String(200), nullable=True)
    heat_increase_rate = db.Column(db.String(200), nullable=True)
    filename = db.Column(db.String(300))

    def __repr__(self):
        return "<SentMail %r>" % self.id


with app.app_context():
    db.create_all()


@app.route("/", methods=["POST", "GET"])
def index():
    emails = Mail.query.order_by(Mail.id).all()
    for email in emails:
        if email.filename and email.filename.endswith(".csv"):
            csv_path = os.path.join(app.config["UPLOAD_FOLDER"], email.filename)
            with open(csv_path, mode="r", encoding="utf-8") as csv_file:
                csv_reader = csv.reader(csv_file)
                email.csv_data = list(csv_reader)
        else:
            email.csv_data = None
    return render_template("index.html", emails=emails)


@app.route("/send_email", methods=["POST"])
def send_email():
    sample_id = request.form["sample_id"]
    serial_number = request.form["serial_number"]
    sample_weight = request.form["sample_weight"]
    heat_interval = request.form["heat_interval"]
    heat_increase_rate = request.form["heat_increase_rate"]
    file = request.files["file"]
    filename = secure_filename(file.filename) if file else None

    if file:
        # Save the file to the upload folder
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    new_message = Mail(
        sample_id=sample_id,
        serial_number=serial_number,
        sample_weight=sample_weight,
        heat_interval=heat_interval,
        heat_increase_rate=heat_increase_rate,
        filename=filename,
    )

    try:
        db.session.add(new_message)
        db.session.commit()
        flash("Data stored successfully")
        return redirect(url_for("index"))
    except:
        flash("There was an issue storing the Data")
        return redirect(url_for("index"))


@app.route("/delete_all", methods=["POST"])
def delete_all():
    try:
        db.session.query(Mail).delete()
        db.session.commit()
        flash("All csv data deleted successfully")
    except:
        db.session.rollback()
        flash("There was an issue deleting the csv data's")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
