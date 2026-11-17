
import numpy as np
import pandas as pd


def explain_flight_prediction(model, flight_data):
    """
    Explain an individual prediction using the
    Logistic Regression decision function.

    flight_data must contain the model's original
    eight input features.
    """

    if not hasattr(model, "named_steps"):
        raise ValueError("Expected a sklearn Pipeline.")

    preprocessor = model.named_steps["preprocessor"]
    classifier = model.named_steps["classifier"]

    if classifier.__class__.__name__ != "LogisticRegression":
        raise ValueError(
            "This explanation currently supports LogisticRegression."
        )

    input_df = pd.DataFrame([flight_data])

    transformed = preprocessor.transform(input_df)

    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()

    feature_names = preprocessor.get_feature_names_out()

    coefficients = classifier.coef_[0]

    transformed_values = np.asarray(transformed)[0]

    contributions = transformed_values * coefficients

    feature_details = []

    for name, contribution in zip(
        feature_names, contributions
    ):
        if abs(contribution) < 1e-10:
            continue

        feature_details.append({
            "feature": name,
            "contribution": float(contribution),
            "direction": (
                "Increases delay score"
                if contribution > 0
                else "Decreases delay score"
            ),
            "magnitude": abs(float(contribution)),
        })

    feature_details.sort(
        key=lambda item: item["magnitude"],
        reverse=True
    )

    decision_score = float(
        classifier.decision_function(transformed)[0]
    )

    return {
        "decision_score": decision_score,
        "explanations": feature_details[:15],
    }
