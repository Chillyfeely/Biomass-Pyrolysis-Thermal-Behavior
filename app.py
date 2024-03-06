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


class CsvData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    csv_filename = db.Column(db.String(300), nullable=True)
    time = db.Column(db.Float, nullable=True)
    unsubtracted_weight = db.Column(db.Float, nullable=True)
    baseline_weight = db.Column(db.Float, nullable=True)
    program_temperature = db.Column(db.Float, nullable=True)
    sample_temperature = db.Column(db.Float, nullable=True)
    approx_gas_flow = db.Column(db.Float, nullable=True)
    unsubtracted_delta_t = db.Column(db.Float, nullable=True)
    baseline_delta_t = db.Column(db.Float, nullable=True)
    unsubtracted_heat_flow = db.Column(db.Float, nullable=True)
    baseline_heat_flow = db.Column(db.Float, nullable=True)
    heat_flow_calibration = db.Column(db.Float, nullable=True)
    unsubtracted_microvolt = db.Column(db.Float, nullable=True)
    r25_diagnostic_temperature = db.Column(db.Float, nullable=True)


with app.app_context():
    db.create_all()


@app.route("/", methods=["POST", "GET"])
def index():
    emails = Mail.query.order_by(Mail.id).all()
    for email in emails:
        if email.filename and email.filename.endswith(".csv"):
            email.csv_data = CsvData.query.filter_by(csv_filename=email.filename).all()
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
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

    new_message = Mail(
        sample_id=sample_id,
        serial_number=serial_number,
        sample_weight=sample_weight,
        heat_interval=heat_interval,
        heat_increase_rate=heat_increase_rate,
        filename=filename,
    )

    with open(file_path, mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip the header row
        for row in csv_reader:
            csv_data = CsvData(
                csv_filename=filename,
                time=row[0],
                unsubtracted_weight=row[1],
                baseline_weight=row[2],
                program_temperature=row[3],
                sample_temperature=row[4],
                approx_gas_flow=row[5],
                unsubtracted_delta_t=row[6],
                baseline_delta_t=row[7],
                unsubtracted_heat_flow=row[8],
                baseline_heat_flow=row[9],
                heat_flow_calibration=row[10],
                unsubtracted_microvolt=row[11],
                r25_diagnostic_temperature=row[12],
            )
            db.session.add(csv_data)

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
        db.session.query(CsvData).delete()
        db.session.commit()
        flash("All csv data deleted successfully")
    except:
        db.session.rollback()
        flash("There was an issue deleting the csv data's")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
