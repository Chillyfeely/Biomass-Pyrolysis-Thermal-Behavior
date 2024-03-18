def printGraph1():
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import json
    import plotly

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces

    # Define a list of file paths for your CSV files
    csv_files = [
        "./Formatted/M1.csv",
        "./Formatted/M2.csv",
        "./Formatted/M3.csv",
        "./Formatted/M4.csv",
        "./Formatted/M5.csv",
    ]

    DTGvalues = [
        "DTG 10 oC/min",
        "DTG 20 oC/min",
        "DTG 30 oC/min",
        "DTG 40 oC/min",
        "DTG 50 oC/min",
    ]
    TGvalues = [
        "TG 10 oC/min",
        "TG 20 oC/min",
        "TG 30 oC/min",
        "TG 40 oC/min",
        "TG 50 oC/min",
    ]

    # Initialize an empty list
    # Read data from each CSV file and append to the list
    for filename, dtgval in zip(csv_files, DTGvalues):
        data = pd.read_csv(filename)
        fig.add_trace(
            go.Scatter(
                x=data["Temp oC"],
                y=data["DTG"],
                mode="lines",
                name=dtgval,
                line=dict(shape="spline", smoothing=1.3),
            ),
            secondary_y=False,
        )

    # Read data from each CSV file and append to the list
    for filename, tgval in zip(csv_files, TGvalues):
        data = pd.read_csv(filename)
        fig.add_trace(
            go.Scatter(
                x=data["Temp oC"], y=data["TG % or wt%"], mode="lines", name=tgval
            ),
            secondary_y=True,
        )

    fig.update_layout(
        title_text="TG and DTG curves indicating the percent mass loss of biomass at five different heating rates."
    )

    # Set x-axis title
    fig.update_xaxes(title_text="Temp oC")

    # Set y-axes titles
    fig.update_yaxes(title_text="DTG (% min-1)", secondary_y=False)
    fig.update_yaxes(title_text="TG % or wt%", secondary_y=True)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


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
        title="DSC curves indicating heat flow to-and-from biomass at five different heating rates.",
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
        title="DTA curves indicating heat flow to-and-from biomass at five different heating rates.",
        xaxis_title="Temp oC",
        yaxis_title="DTA microvolt",
    )
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


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
    new_df["DTG"] = new_df["DTG % min-1, mg oC-1"].rolling(window=500).mean()
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
