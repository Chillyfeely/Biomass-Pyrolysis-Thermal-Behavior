from flask import (
    Flask,
    render_template,
    url_for,
    request,
    redirect,
    flash,
    session,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from werkzeug.utils import secure_filename
import os, csv, time, baty
from flask_paginate import Pagination

# <- Yapay Zeka ->
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///biomass.db"
app.config["SECRET_KEY"] = os.urandom(24)
app.config["UPLOAD_FOLDER"] = "Uploaded"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db = SQLAlchemy(app)


class Mail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.String(200), nullable=True)
    serial_number = db.Column(db.String(200), nullable=True)
    sample_weight = db.Column(db.String(200), nullable=True)
    heat_interval = db.Column(db.String(200), nullable=True)
    heat_increase_rate = db.Column(db.Integer, nullable=True)
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
    DTG1 = db.Column(db.String, nullable=True)
    DTG2 = db.Column(db.String, nullable=True)
    DSC = db.Column(db.String, nullable=True)
    DTA = db.Column(db.String, nullable=True)
    m_mg = db.Column(db.String, nullable=True)
    mo_m = db.Column(db.String, nullable=True)
    mo_m_alpha = db.Column(db.String, nullable=True)
    alpha = db.Column(db.String, nullable=True)
    d_alpha_dT = db.Column(db.String, nullable=True)
    ln_beta_d_alpha_dT = db.Column(db.String, nullable=True)
    one_over_T = db.Column(db.String, nullable=True)
    T_squared = db.Column(db.String, nullable=True)
    ln_beta_over_T_squared = db.Column(db.String, nullable=True)


class AiAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_label = db.Column(db.String(200), nullable=True)
    tga_filename = db.Column(db.String(300))
    dtg_filename = db.Column(db.String(300))
    lstm_score = db.Column(db.Float, nullable=True)


with app.app_context():
    db.create_all()


@app.route("/seeRawData", methods=["POST", "GET"])
def seeRawData():
    search = False
    q = request.args.get("q")
    if q:
        search = True

    emails = Mail.query.order_by(Mail.id).all()

    paginated_data = []
    for email in emails:
        if email.filename and email.filename.endswith(".csv"):
            page = session.get(
                f"page_{email.filename}", 1
            )  # Get the current page number from the session
            per_page = 1000

            csv_data = CsvData.query.filter_by(csv_filename=email.filename)
            total = csv_data.count()
            csv_data = csv_data.offset((page - 1) * per_page).limit(per_page).all()
            pagination = Pagination(
                page=page,
                total=total,
                per_page=per_page,
                search=search,
                record_name="csv_data",
            )
            paginated_data.append((email, csv_data, pagination))
        else:
            paginated_data.append((email, None, None))

    return render_template("seeRawData.html", paginated_data=paginated_data)


@app.route("/uploadData")
def uploadData():
    return render_template("uploadData.html")


@app.route("/printGraph")
def printGraph():
    graphJSON1 = baty.printGraph1()
    graphJSON2 = baty.printGraph2()
    graphJSON3 = baty.printGraph3()
    return render_template(
        "printGraph.html",
        graphJSON1=graphJSON1,
        graphJSON2=graphJSON2,
        graphJSON3=graphJSON3,
    )


@app.route("/home")
def home():
    return render_template("index.html")


@app.route("/requestAiAnalysis", methods=["POST", "GET"])
def requestAiAnalysis():
    return render_template("requestAiAnalysis.html")


@app.route("/seeAiAnalysis", methods=["POST", "GET"])
def seeAiAnalysis():
    analyses = AiAnalysis.query.all()  # Query the database
    return render_template("seeAiAnalysis.html", analyses=analyses)


@app.route("/", methods=["POST", "GET"])
def index():
    return render_template("index.html")


@app.route("/change_page/<filename>", methods=["POST"])
def change_page(filename):
    page = request.form.get(
        "page", type=int, default=1
    )  # Get the new page number from the form
    session[f"page_{filename}"] = page  # Store the new page number in the session
    return render_template("seeRawData.html")  # Redirect to the 'seeData' page


@app.route("/analyze_with_ai", methods=["POST"])
def analyze_with_ai():
    data_label = request.form["data_label"]
    file = request.files["file"]
    filename = secure_filename(file.filename) if file else None

    if file:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

    lstm_model = load_model("my_model.keras")

    df = pd.read_excel(file_path)

    val_df = df[df["Isıtma Hızı"] == 10]

    train_df = df
    dataset = train_df.values.astype("float32")
    train_df = pd.DataFrame(dataset, columns=train_df.columns, index=train_df.index)
    train_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    train_df.dropna(inplace=True)
    train_df = train_df.replace(np.inf, 0)

    X_train = train_df.iloc[:, :-1]
    y_train = train_df.iloc[:, -1]
    X_val = val_df.iloc[:, :-1]
    y_val = val_df.iloc[:, -1]

    temperature = X_val.iloc[:, -1]
    predictions = lstm_model.predict(X_val)
    lstm_score = r2_score(y_val, predictions)
    session["analysis_status"] = "processing"

    def plot_predictions(real, predicted, t, plot_type):
        fig, ax = plt.subplots(figsize=(16, 4))
        if plot_type == 1:
            r_label = "Actual TG (m)"
            p_label = "Predicted TG (m)"
            y_label = "Normalized biomass scale (TG %)"
            title = "TG predictions of proposed model"
        else:
            r_label = "Actual DTG (m)"
            p_label = "Predicted DTG (m)"
            y_label = "Normalized biomass scale (DTG %)"
            title = "DTG predictions of proposed model"

        ax.plot(real, label=r_label)
        ax.plot(predicted, label=p_label)

        ax.set_title(title)
        ax.set_xlabel("Temperature (°C)")
        ax.set_ylabel(y_label)
        plt.grid(True)
        ax.legend()
        return fig, ax

    tga_orig = y_val / y_val.iloc[0] * 100
    tga_pred = predictions / predictions[0] * 100
    tga_pred = pd.Series(tga_pred[:, 0])

    temp = X_val["Sıcaklık"]

    tga_orig = tga_orig.replace([np.inf, -np.inf], np.nan)
    tga_pred = tga_pred.replace([np.inf, -np.inf], np.nan)

    tga_orig = tga_orig.rolling(500).sum()
    tga_pred = tga_pred.rolling(500).sum()

    tga_orig = tga_orig.bfill()
    tga_pred = tga_pred.bfill()
    dtg_orig = tga_orig.diff() / temp.diff()
    dtg_pred = tga_pred.diff() / temp.diff()

    dtg_orig = dtg_orig.replace([np.inf, -np.inf], np.nan)
    dtg_pred = dtg_pred.replace([np.inf, -np.inf], np.nan)

    dtg_orig = dtg_orig.bfill()
    dtg_pred = dtg_pred.bfill()

    dtg_orig = dtg_orig.rolling(500).sum()
    dtg_pred = dtg_pred.rolling(500).sum()

    dtg_orig = dtg_orig.fillna(0.0)
    dtg_pred = dtg_pred.fillna(0.0)

    fig, ax = plot_predictions(tga_orig, tga_pred, temp, 1)
    fig.savefig(f"static/Formatted/images/{filename}_tga_plot.png")

    fig, ax = plot_predictions(dtg_orig, dtg_pred, temp, 0)
    fig.savefig(f"static/Formatted/images/{filename}_dtg_plot.png")

    new_analysis = AiAnalysis(
        data_label=data_label,
        tga_filename=f"static/Formatted/images/{filename}_tga_plot.png",
        dtg_filename=f"static/Formatted/images/{filename}_dtg_plot.png",
        lstm_score=lstm_score,
    )
    try:
        db.session.add(new_analysis)
        db.session.commit()
        flash("Data stored successfully")
        return render_template("seeAiAnalysis.html")
    except:
        flash("There was an issue storing the Data")
        return render_template("requestAiAnalysis.html")


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
        baty.formatted_data_precision(
            file_path, int(heat_increase_rate), f"Formatted/{filename}"
        )
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
                DTG1=row[4],
                DTG2=row[5],
                DSC=row[6],
                DTA=row[7],
                m_mg=row[8],
                mo_m=row[9],
                mo_m_alpha=row[10],
                alpha=row[11],
                d_alpha_dT=row[12],
                ln_beta_d_alpha_dT=row[13],
                one_over_T=row[14],
                T_squared=row[15],
                ln_beta_over_T_squared=row[16],
            )
            db.session.add(csv_data)

    try:
        db.session.add(new_message)
        db.session.commit()
        flash("Data stored successfully")
        return render_template("uploadData.html")
    except:
        flash("There was an issue storing the Data")
        return render_template("uploadData.html")


@app.route("/delete_all", methods=["POST"])
def delete_all():
    try:
        db.session.query(Mail).delete()
        db.session.query(CsvData).delete()
        db.session.query(AiAnalysis).delete()
        db.session.commit()
        flash("All csv data deleted successfully")
    except:
        db.session.rollback()
        flash("There was an issue deleting the csv data's")
    return render_template("seeRawData.html")


if __name__ == "__main__":
    app.run(debug=True)
