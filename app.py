from flask import Flask, render_template, request
from flask_cors import CORS
import os
import numpy as np
import pandas as pd

from mlProject.pipeline.prediction import PredictionPipeline

app = Flask(__name__)
CORS(app)

# Order must match the training feature columns (schema.yaml COLUMNS minus the target).
FEATURE_COLUMNS = [
    "fixed acidity",
    "volatile acidity",
    "citric acid",
    "residual sugar",
    "chlorides",
    "free sulfur dioxide",
    "total sulfur dioxide",
    "density",
    "pH",
    "sulphates",
    "alcohol",
]


@app.route("/", methods=["GET"])
def home_page():
    return render_template("index.html")


@app.route("/train", methods=["GET"])
def training():
    os.system("python main.py")
    return "Training successful!"


@app.route("/predict", methods=["POST"])
def predict():
    try:
        values = [float(request.form[col]) for col in FEATURE_COLUMNS]
        data = pd.DataFrame([values], columns=FEATURE_COLUMNS)

        obj = PredictionPipeline()
        prediction = obj.predict(data)

        return render_template(
            "results.html", prediction=round(float(prediction[0]), 2)
        )
    except Exception as e:
        print("The Exception message is: ", e)
        return "Something went wrong"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
