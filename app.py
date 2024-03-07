from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os, csv, time

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
    Time = db.Column(db.String, nullable=True)
    Temp_oC = db.Column(db.String, nullable=True)
    Temp_K = db.Column(db.String, nullable=True)
    TG = db.Column(db.String, nullable=True)
    DTG = db.Column(db.String, nullable=True)
    DSC = db.Column(db.String, nullable=True)
    DTA = db.Column(db.String, nullable=True)
    m = db.Column(db.String, nullable=True)
    mo_m = db.Column(db.String, nullable=True)
    mo_m_alpha = db.Column(db.String, nullable=True)
    alpha = db.Column(db.String, nullable=True)
    d_alpha_dT = db.Column(db.String, nullable=True)
    ln_beta_d_alpha_dT = db.Column(db.String, nullable=True)
    one_over_T = db.Column(db.String, nullable=True)
    T_squared = db.Column(db.String, nullable=True)
    ln_beta_over_T_squared = db.Column(db.String, nullable=True)


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
        formatted_data_precision(file_path, 10, f"Formatted/{filename}")
        file_path2 = f"Formatted/{filename}"

        while not os.path.exists(file_path2):
            time.sleep(1)

    new_message = Mail(
        sample_id=sample_id,
        serial_number=serial_number,
        sample_weight=sample_weight,
        heat_interval=heat_interval,
        heat_increase_rate=heat_increase_rate,
        filename=filename,
    )

    with open(file_path2, mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)
        for row in csv_reader:
            csv_data = CsvData(
                csv_filename=filename,
                Time=row[0],
                Temp_oC=row[1],
                Temp_K=row[2],
                TG=row[3],
                DTG=row[4],
                DSC=row[5],
                DTA=row[6],
                m=row[7],
                mo_m=row[8],
                mo_m_alpha=row[9],
                alpha=row[10],
                d_alpha_dT=row[11],
                ln_beta_d_alpha_dT=row[12],
                one_over_T=row[13],
                T_squared=row[14],
                ln_beta_over_T_squared=row[15],
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


# <-Batuhanın Fonksiyonları->
def calculate_log_beta_dt(x, beta):
    import numpy as np
    import math

    if x > 0:
        return math.log(x * beta)
    else:
        return np.nan


def calculate_log_beta_t(x, beta):
    import numpy as np
    import math

    if x > 0:
        return math.log(beta / x)
    else:
        return np.nan


def formatted_data(filePath, beta, path):
    import pandas as pd

    df = pd.read_csv(filePath)  # Sadece exceli csv yap kodaki csv okur hale gelir
    new_df = pd.DataFrame()
    m0 = df["Unsubtracted Weight"].iloc[0]
    malpha = df["Unsubtracted Weight"].iloc[-1]
    beta = beta
    new_df["Time"] = df["Time"]
    new_df["Temp oC"] = df["Sample Temperature"]
    new_df["Temp K"] = df["Sample Temperature"] + 273.15
    new_df["TG % or wt%"] = (df["Unsubtracted Weight"] / m0) * 100
    new_df["DTG % min-1, mg oC-1"] = new_df["TG % or wt%"].diff(1) / new_df[
        "Time"
    ].diff(1)
    new_df["DTG % min-1, mg oC-1"] = new_df["DTG % min-1, mg oC-1"].shift(-1)
    new_df["DTG"] = "#N/A"
    new_df["DSC mW mg-1"] = df["Unsubtracted Heat Flow"]
    new_df["DTA microvolt"] = df["Unsubstracted Microvolt"]
    new_df["m mg"] = df["Unsubtracted Weight"]
    new_df["mo - m mg"] = m0 - df["Unsubtracted Weight"]
    new_df["mo - mα mg"] = malpha - m0
    new_df["α"] = new_df["mo - m mg"] / new_df["mo - mα mg"]
    new_df["dα / dT % K-1"] = new_df["α"].diff(1) / -new_df["Temp K"].diff(1)
    new_df["dα / dT % K-1"] = new_df["dα / dT % K-1"].shift(-1)
    new_df["ln(β*(dα / dT))"] = new_df["dα / dT % K-1"].apply(
        calculate_log_beta_dt, args=(beta,)
    )
    new_df["1/T"] = 1 / new_df["Temp oC"]
    new_df["T²"] = new_df["Temp K"] * new_df["Temp K"]
    new_df["ln(β/T²)"] = new_df["T²"].apply(calculate_log_beta_t, args=(beta,))
    new_df.to_csv(path, index=False)  # index istiyosan index=True yaparsin
    return new_df  # buda senin gormen icin geri alip bakabilirsin


# Tek farki var noktadan sonraki 6 satir gozukuyo sadece bunda
def formatted_data_precision(filePath, beta, path):
    import pandas as pd

    df = pd.read_csv(filePath)
    new_df = pd.DataFrame()
    m0 = df["Unsubtracted Weight"].iloc[0]
    malpha = df["Unsubtracted Weight"].iloc[-1]
    beta = beta
    new_df["Time"] = df["Time"]
    new_df["Temp oC"] = df["Sample Temperature"]
    new_df["Temp K"] = (df["Sample Temperature"] + 273.15).apply(lambda x: round(x, 6))
    new_df["TG % or wt%"] = ((df["Unsubtracted Weight"] / m0) * 100).apply(
        lambda x: round(x, 6)
    )
    new_df["DTG % min-1, mg oC-1"] = (
        new_df["TG % or wt%"].diff(1) / new_df["Time"].diff(1)
    ).apply(lambda x: round(x, 6))
    new_df["DTG % min-1, mg oC-1"] = new_df["DTG % min-1, mg oC-1"].shift(-1)
    new_df["DTG"] = "#N/A"
    new_df["DSC mW mg-1"] = df["Unsubtracted Heat Flow"]
    new_df["DTA microvolt"] = df["Unsubstracted Microvolt"]
    new_df["m mg"] = df["Unsubtracted Weight"]
    new_df["mo - m mg"] = (m0 - df["Unsubtracted Weight"]).apply(lambda x: round(x, 6))
    new_df["mo - mα mg"] = malpha - m0
    new_df["α"] = (new_df["mo - m mg"] / new_df["mo - mα mg"]).apply(
        lambda x: round(x, 6)
    )
    new_df["dα / dT % K-1"] = (new_df["α"].diff(1) / -new_df["Temp K"].diff(1)).apply(
        lambda x: round(x, 6)
    )
    new_df["dα / dT % K-1"] = new_df["dα / dT % K-1"].shift(-1)
    new_df["ln(β*(dα / dT))"] = (
        new_df["dα / dT % K-1"]
        .apply(calculate_log_beta_dt, args=(beta,))
        .apply(lambda x: round(x, 6))
    )
    new_df["1/T"] = (1 / new_df["Temp oC"]).apply(lambda x: round(x, 6))
    new_df["T²"] = (new_df["Temp K"] * new_df["Temp K"]).apply(lambda x: round(x, 6))
    new_df["ln(β/T²)"] = (
        new_df["T²"]
        .apply(calculate_log_beta_t, args=(beta,))
        .apply(lambda x: round(x, 6))
    )
    new_df.to_csv(path, index=False)  # index istiyosan index=True yaparsin
    return new_df  # buda senin gormen icin geri alip bakabilirsin


if __name__ == "__main__":
    app.run(debug=True)
