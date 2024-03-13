from flask import Flask, render_template, url_for, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os, csv, time
from flask_paginate import Pagination


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
    graphJSON2 = printGraph2()
    graphJSON3 = printGraph3()
    return render_template(
        "printGraph.html", graphJSON2=graphJSON2, graphJSON3=graphJSON3
    )


def printGraph2():
    import plotly
    import pandas as pd
    import plotly.express as px
    import json

    # Define a list of file paths for your CSV files
    csv_files = [
        "./Formatted/M1.csv",
        "./Formatted/M2.csv",
        "./Formatted/M3.csv",
        "./Formatted/M4.csv",
        "./Formatted/M5.csv",
    ]

    # Define a color list for lines (modify with desired colors)
    betas = ["10 oC/min", "20 oC/min", "30 oC/min", "40 oC/min", "50 oC/min"]

    # Initialize an empty list
    all_data = []

    # Read data from each CSV file and append to the list
    for filename, beta in zip(csv_files, betas):
        data = pd.read_csv(filename)
        data["N^2"] = beta
        all_data.append(data)

    # Concatenate all DataFrames into a single DataFrame (optional)
    combined_data = pd.concat(all_data, ignore_index=True)

    # Create a scatter plot with markers and customize appearance
    fig = px.scatter(
        combined_data, x="Temp oC", y="DSC mW mg-1", color="N^2"
    )  # Adjust opacity and size as needed

    # Customize the plot
    fig.update_layout(
        title="Graph 2",
        xaxis_title="Temp oC",
        yaxis_title="DSC (mW mg-1)",
    )

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


def printGraph3():
    import plotly, json
    import pandas as pd
    import plotly.express as px

    # Define a list of file paths for your CSV files
    csv_files = [
        "./Formatted/M1.csv",
        "./Formatted/M2.csv",
        "./Formatted/M3.csv",
        "./Formatted/M4.csv",
        "./Formatted/M5.csv",
    ]

    # Define a color list for lines (modify with desired colors)
    betas = ["10 oC/min", "20 oC/min", "30 oC/min", "40 oC/min", "50 oC/min"]

    # Initialize an empty list
    all_data = []

    # Read data from each CSV file and append to the list
    for filename, beta in zip(csv_files, betas):
        data = pd.read_csv(filename)
        data["N^2"] = beta
        all_data.append(data)

    # Concatenate all DataFrames into a single DataFrame (optional)
    combined_data = pd.concat(all_data, ignore_index=True)

    # Create a scatter plot with markers and customize appearance
    fig = px.scatter(
        combined_data, x="Temp oC", y="DTA microvolt", color="N^2"
    )  # Adjust opacity and size as needed

    # Customize the plot
    fig.update_layout(
        title="Graph 3",
        xaxis_title="Temp oC",
        yaxis_title="DTA microvolt",
    )
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


@app.route("/home")
def home():
    return render_template("index.html")


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
        formatted_data_precision(
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
        db.session.commit()
        flash("All csv data deleted successfully")
    except:
        db.session.rollback()
        flash("There was an issue deleting the csv data's")
    return render_template("seeRawData.html")


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

    df = pd.read_csv(filePath)
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
    new_df.to_csv(path, index=False)
    return new_df


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
    new_df["mo - mα mg"] = (m0 - malpha).round(6)
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
    new_df.to_csv(path, index=False, na_rep="null")
    return new_df


if __name__ == "__main__":
    app.run(debug=True)
