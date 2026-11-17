
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    balanced_accuracy_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
    OrdinalEncoder,
)
from sklearn.inspection import permutation_importance
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"

TARGET = "DepDel15"

FEATURES = [
    "Year",
    "Month",
    "DayofMonth",
    "DayOfWeek",
    "Origin",
    "Dest",
    "CRSDepTime",
    "Distance",
]

NUMERIC_FEATURES = [
    "Year",
    "Month",
    "DayofMonth",
    "DayOfWeek",
    "CRSDepTime",
    "Distance",
]

CATEGORICAL_FEATURES = [
    "Origin",
    "Dest",
]

REQUIRED_COLUMNS = FEATURES + [
    TARGET,
    "Cancelled",
    "Diverted",
]

MONTHS = [7, 8, 9, 10, 11, 12]

MONTHLY_SAMPLE_SIZE = 100_000
TUNING_SAMPLE_SIZE = 60_000

RANDOM_STATE = 42

OUTPUT_MODEL = BASE_DIR / "flight_delay_model_best.joblib"
OUTPUT_THRESHOLD = BASE_DIR / "best_model_threshold.txt"

OUTPUT_COMPARISON = BASE_DIR / "algorithm_comparison.csv"
OUTPUT_FINAL_RESULTS = BASE_DIR / "best_model_final_results.csv"
OUTPUT_THRESHOLD_ANALYSIS = BASE_DIR / "best_model_threshold_analysis.csv"

OUTPUT_IMPORTANCE_CSV = BASE_DIR / "best_model_feature_importance.csv"
OUTPUT_IMPORTANCE_PNG = BASE_DIR / "best_model_feature_importance.png"

OUTPUT_PERMUTATION_CSV = (
    BASE_DIR / "permutation_feature_importance.csv"
)

OUTPUT_PERMUTATION_PNG = (
    BASE_DIR / "permutation_feature_importance.png"
)

OUTPUT_ERRORS_CSV = (
    BASE_DIR / "prediction_errors.csv"
)

OUTPUT_CALIBRATION_CSV = (
    BASE_DIR / "calibration_results.csv"
)

OUTPUT_CALIBRATION_PNG = (
    BASE_DIR / "calibration_plot.png"
)
# ============================================================
# 2. LOAD DATASETS
# ============================================================

def load_datasets():

    print("\nLoading monthly datasets...")

    frames = []

    for month in MONTHS:

        file_path = DATASET_DIR / f"Flights_2022_{month}.csv"

        if not file_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {file_path}"
            )

        print(f"\nLoading: {file_path.name}")

        df = pd.read_csv(
            file_path,
            usecols=lambda column: column in REQUIRED_COLUMNS,
            low_memory=False,
        )

        missing = [
            column
            for column in REQUIRED_COLUMNS
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing columns in {file_path.name}: {missing}"
            )

        print(f"Original rows: {len(df):,}")

        if len(df) > MONTHLY_SAMPLE_SIZE:
            df = df.sample(
                n=MONTHLY_SAMPLE_SIZE,
                random_state=RANDOM_STATE,
            )

        print(f"Selected rows: {len(df):,}")

        frames.append(df)

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    print("\nCombined dataset:", combined.shape)

    return combined


# ============================================================
# 3. CLEAN DATA
# ============================================================

def clean_dataset(df):

    print("\nCleaning dataset...")

    df = df.copy()

    for column in [TARGET, "Cancelled", "Diverted"]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df[
        (df["Cancelled"] == 0)
        & (df["Diverted"] == 0)
    ].copy()

    df = df[
        df[TARGET].isin([0, 1])
    ].copy()

    for column in NUMERIC_FEATURES:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    for column in CATEGORICAL_FEATURES:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    df = df.dropna(
        subset=[
            "Month",
            TARGET,
            "Origin",
            "Dest",
        ]
    )

    df = df.drop_duplicates(
        subset=FEATURES + [TARGET]
    )

    df[TARGET] = df[TARGET].astype(int)

    print(f"Cleaned records: {len(df):,}")

    print("\nDelay distribution:")
    print(df[TARGET].value_counts().sort_index())

    return df.reset_index(drop=True)


# ============================================================
# 4. CHRONOLOGICAL DATA SPLIT
# ============================================================

def split_data(df):

    print("\nCreating chronological data splits...")

    train_df = df[
        df["Month"].isin([7, 8, 9, 10])
    ].copy()

    validation_df = df[
        df["Month"] == 11
    ].copy()

    test_df = df[
        df["Month"] == 12
    ].copy()

    if (
        train_df.empty
        or validation_df.empty
        or test_df.empty
    ):
        raise ValueError(
            "A data split is empty. Check the Month column."
        )

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]

    X_validation = validation_df[FEATURES]
    y_validation = validation_df[TARGET]

    X_test = test_df[FEATURES]
    y_test = test_df[TARGET]

    print(f"Training: {len(X_train):,}")
    print(f"Validation: {len(X_validation):,}")
    print(f"Final test: {len(X_test):,}")

    return (
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
    )


# ============================================================
# 5. CREATE TUNING SAMPLE
# ============================================================

def create_tuning_sample(X_train, y_train):

    print("\nPreparing tuning sample...")

    frame = pd.concat(
        [
            X_train,
            y_train.rename(TARGET),
        ],
        axis=1,
    )

    total_records = len(frame)

    sample_size = min(
        TUNING_SAMPLE_SIZE,
        total_records,
    )

    parts = []

    for class_value, group in frame.groupby(TARGET):

        count = round(
            sample_size * len(group) / total_records
        )

        count = min(count, len(group))

        if count > 0:
            parts.append(
                group.sample(
                    n=count,
                    random_state=RANDOM_STATE,
                )
            )

    tuning_df = pd.concat(
        parts,
        ignore_index=True,
    )

    tuning_df = tuning_df.sample(
        frac=1,
        random_state=RANDOM_STATE,
    ).reset_index(drop=True)

    X_tuning = tuning_df[FEATURES]
    y_tuning = tuning_df[TARGET]

    print(f"Tuning records: {len(tuning_df):,}")
    print("\nTuning class distribution:")
    print(y_tuning.value_counts().sort_index())

    return X_tuning, y_tuning


# ============================================================
# 6. PREPROCESSING FOR TREE AND LOGISTIC MODELS
# ============================================================

def create_onehot_preprocessor():

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    min_frequency=10,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ]
    )


# ============================================================
# 7. PREPROCESSING FOR HIST GRADIENT BOOSTING
# ============================================================

def create_ordinal_preprocessor():

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "encoder",
                OrdinalEncoder(
                    handle_unknown="use_encoded_value",
                    unknown_value=-1,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ],
        sparse_threshold=0,
    )


# ============================================================
# 8. CREATE ALGORITHMS
# ============================================================

def create_model(model_name):

    if model_name == "Random Forest":

        classifier = RandomForestClassifier(
            n_estimators=60,
            max_depth=18,
            min_samples_leaf=10,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=1,
        )

        return Pipeline(
            steps=[
                ("preprocessor", create_onehot_preprocessor()),
                ("classifier", classifier),
            ]
        )

    elif model_name == "Extra Trees":

        classifier = ExtraTreesClassifier(
            n_estimators=60,
            max_depth=18,
            min_samples_leaf=10,
            max_features="sqrt",
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=1,
        )

        return Pipeline(
            steps=[
                ("preprocessor", create_onehot_preprocessor()),
                ("classifier", classifier),
            ]
        )

    elif model_name == "Logistic Regression":

        classifier = LogisticRegression(
            C=0.5,
            class_weight="balanced",
            solver="saga",
            max_iter=500,
            random_state=RANDOM_STATE,
            n_jobs=1,
        )

        return Pipeline(
            steps=[
                ("preprocessor", create_onehot_preprocessor()),
                ("classifier", classifier),
            ]
        )

    elif model_name == "HistGradientBoosting":

        classifier = HistGradientBoostingClassifier(
            max_iter=100,
            learning_rate=0.08,
            max_leaf_nodes=15,
            l2_regularization=1.0,
            random_state=RANDOM_STATE,
        )

        return Pipeline(
            steps=[
                ("preprocessor", create_ordinal_preprocessor()),
                ("classifier", classifier),
            ]
        )

    else:
        raise ValueError(
            f"Unknown model: {model_name}"
        )


# ============================================================
# 9. FIND BEST THRESHOLD
# ============================================================

def find_best_threshold(y_true, probabilities):

    thresholds = np.arange(
        0.20,
        0.81,
        0.01,
    )

    best_threshold = 0.50
    best_f1 = -1

    for threshold in thresholds:

        predictions = (
            probabilities >= threshold
        ).astype(int)

        score = f1_score(
            y_true,
            predictions,
            zero_division=0,
        )

        if score > best_f1:
            best_f1 = score
            best_threshold = float(threshold)

    return best_threshold, best_f1


# ============================================================
# 10. THRESHOLD ANALYSIS
# ============================================================

def analyze_thresholds(y_true, probabilities):

    thresholds = [
        0.30, 0.35, 0.40, 0.45,
        0.47, 0.50, 0.55, 0.60,
        0.65, 0.70,
    ]

    rows = []

    for threshold in thresholds:

        predictions = (
            probabilities >= threshold
        ).astype(int)

        tn, fp, fn, tp = confusion_matrix(
            y_true,
            predictions,
            labels=[0, 1],
        ).ravel()

        rows.append(
            {
                "Threshold": threshold,
                "Accuracy": accuracy_score(
                    y_true,
                    predictions,
                ),
                "Precision": precision_score(
                    y_true,
                    predictions,
                    zero_division=0,
                ),
                "Recall": recall_score(
                    y_true,
                    predictions,
                    zero_division=0,
                ),
                "F1 Score": f1_score(
                    y_true,
                    predictions,
                    zero_division=0,
                ),
                "False Positives": fp,
                "False Negatives": fn,
                "True Positives": tp,
                "True Negatives": tn,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# 11. EVALUATE MODEL
# ============================================================

def evaluate_model(
    model,
    X,
    y,
    threshold,
    dataset_name,
):

    probabilities = model.predict_proba(X)[:, 1]

    predictions = (
        probabilities >= threshold
    ).astype(int)

    results = {
        "Dataset": dataset_name,
        "Threshold": threshold,
        "Accuracy": accuracy_score(y, predictions),
        "Precision": precision_score(
            y,
            predictions,
            zero_division=0,
        ),
        "Recall": recall_score(
            y,
            predictions,
            zero_division=0,
        ),
        "F1 Score": f1_score(
            y,
            predictions,
            zero_division=0,
        ),
        "Balanced Accuracy": balanced_accuracy_score(
            y,
            predictions,
        ),
        "ROC AUC": roc_auc_score(
            y,
            probabilities,
        ),
        "PR AUC": average_precision_score(
            y,
            probabilities,
        ),
    }

    print(f"\n{dataset_name} RESULTS")
    print("=" * 55)

    for name, value in results.items():
        if isinstance(value, (float, np.floating)):
            print(f"{name}: {value:.4f}")
        else:
            print(f"{name}: {value}")

    print("\nConfusion Matrix:")
    print(
        confusion_matrix(
            y,
            predictions,
            labels=[0, 1],
        )
    )

    return results


# ============================================================
# EXPLAINABLE AI AND MODEL RELIABILITY
# ============================================================

def generate_permutation_importance(
    model,
    X_test,
    y_test,
    threshold,
):

    print("\nGENERATING PERMUTATION IMPORTANCE")
    print("=" * 55)

    # Use a manageable sample for 8 GB RAM.
    sample_size = min(20000, len(X_test))

    X_sample = X_test.sample(
        n=sample_size,
        random_state=RANDOM_STATE,
    )

    y_sample = y_test.loc[X_sample.index]

    # Evaluate importance using our selected threshold.
    def threshold_f1_scorer(estimator, X, y):

        probabilities = estimator.predict_proba(X)[:, 1]

        predictions = (
            probabilities >= threshold
        ).astype(int)

        return f1_score(
            y,
            predictions,
            zero_division=0,
        )

    print(f"Evaluation sample: {sample_size:,}")

    importance = permutation_importance(
        model,
        X_sample,
        y_sample,
        scoring=threshold_f1_scorer,
        n_repeats=3,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )

    importance_df = pd.DataFrame({
        "Feature": X_sample.columns,
        "Importance Mean": importance.importances_mean,
        "Importance Std": importance.importances_std,
    })

    importance_df = importance_df.sort_values(
        by="Importance Mean",
        ascending=False,
    )

    importance_df.to_csv(
        OUTPUT_PERMUTATION_CSV,
        index=False,
    )

    # Plot feature importance.
    plot_df = importance_df.sort_values(
        by="Importance Mean",
        ascending=True,
    )

    plt.figure(figsize=(10, 6))

    plt.barh(
        plot_df["Feature"],
        plot_df["Importance Mean"],
        xerr=plot_df["Importance Std"],
    )

    plt.xlabel("Decrease in F1 Score")
    plt.ylabel("Feature")
    plt.title("Permutation Feature Importance")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_PERMUTATION_PNG,
        dpi=300,
    )

    plt.close()

    print("\nTop important features:")
    print(importance_df.to_string(index=False))

    print(f"\nSaved: {OUTPUT_PERMUTATION_CSV}")
    print(f"Saved: {OUTPUT_PERMUTATION_PNG}")


# ============================================================
# FALSE POSITIVE AND FALSE NEGATIVE ANALYSIS
# ============================================================

def analyze_prediction_errors(
    model,
    X_test,
    y_test,
    threshold,
):

    print("\nPREDICTION ERROR ANALYSIS")
    print("=" * 55)

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    predictions = (
        probabilities >= threshold
    ).astype(int)

    error_df = X_test.copy()

    error_df["Actual"] = y_test

    error_df["Predicted"] = predictions

    error_df["Delay Probability"] = probabilities

    error_df["Error Type"] = np.where(
        (y_test == 0) & (predictions == 1),
        "False Positive",
        np.where(
            (y_test == 1) & (predictions == 0),
            "False Negative",
            "Correct",
        ),
    )

    # Keep only incorrect predictions.
    error_df = error_df[
        error_df["Actual"] != error_df["Predicted"]
    ].copy()

    error_df.to_csv(
        OUTPUT_ERRORS_CSV,
        index=False,
    )

    false_positives = (
        error_df["Error Type"] == "False Positive"
    ).sum()

    false_negatives = (
        error_df["Error Type"] == "False Negative"
    ).sum()

    print(f"False positives: {false_positives:,}")
    print(f"False negatives: {false_negatives:,}")
    print(f"Total errors: {len(error_df):,}")

    print(f"\nError report saved: {OUTPUT_ERRORS_CSV}")


# ============================================================
# PROBABILITY CALIBRATION ANALYSIS
# ============================================================

def analyze_probability_calibration(
    model,
    X_test,
    y_test,
):

    print("\nPROBABILITY CALIBRATION ANALYSIS")
    print("=" * 55)

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    # Lower Brier score indicates better probability accuracy.
    brier = brier_score_loss(
        y_test,
        probabilities,
    )

    print(f"Brier Score: {brier:.4f}")

    # Compare predicted probabilities with actual delay frequency.
    actual_fraction, predicted_mean = calibration_curve(
        y_test,
        probabilities,
        n_bins=10,
        strategy="quantile",
    )

    calibration_df = pd.DataFrame({
        "Mean Predicted Probability": predicted_mean,
        "Actual Delay Frequency": actual_fraction,
    })

    calibration_df.to_csv(
        OUTPUT_CALIBRATION_CSV,
        index=False,
    )

    # Plot calibration curve.
    plt.figure(figsize=(8, 6))

    plt.plot(
        predicted_mean,
        actual_fraction,
        marker="o",
        label="Model calibration",
    )

    plt.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        label="Perfect calibration",
    )

    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Actual Delay Frequency")
    plt.title("Flight Delay Probability Calibration")

    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        OUTPUT_CALIBRATION_PNG,
        dpi=300,
    )

    plt.close()

    print("\nCalibration results:")
    print(calibration_df.to_string(index=False))

    print(f"\nSaved: {OUTPUT_CALIBRATION_CSV}")
    print(f"Saved: {OUTPUT_CALIBRATION_PNG}")


   
# ============================================================
# 13. MAIN ALGORITHM COMPARISON
# ============================================================

def main():

    print("\nAIRLINE FLIGHT DELAY ALGORITHM COMPARISON")
    print("=" * 60)

    # Step 1: Load data
    df = load_datasets()

    # Step 2: Clean data
    df = clean_dataset(df)

    # Step 3: Split data chronologically
    (
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
    ) = split_data(df)

    # Step 4: Create tuning sample
    X_tuning, y_tuning = create_tuning_sample(
        X_train,
        y_train,
    )

    model_names = [
        "Random Forest",
        "Extra Trees",
        "Logistic Regression",
        "HistGradientBoosting",
    ]

    comparison_results = []

    best_model_name = None
    best_threshold = 0.50
    best_validation_f1 = -1

    # Step 5: Compare algorithms
    for model_name in model_names:

        print("\n" + "=" * 60)
        print(f"TRAINING: {model_name}")
        print("=" * 60)

        model = create_model(model_name)

        model.fit(X_tuning, y_tuning)

        probabilities = model.predict_proba(
            X_validation
        )[:, 1]

        threshold, _ = find_best_threshold(
            y_validation,
            probabilities,
        )

        predictions = (
            probabilities >= threshold
        ).astype(int)

        result = {
            "Algorithm": model_name,
            "Threshold": threshold,
            "Accuracy": accuracy_score(
                y_validation, predictions
            ),
            "Precision": precision_score(
                y_validation,
                predictions,
                zero_division=0,
            ),
            "Recall": recall_score(
                y_validation,
                predictions,
                zero_division=0,
            ),
            "F1 Score": f1_score(
                y_validation,
                predictions,
                zero_division=0,
            ),
            "PR AUC": average_precision_score(
                y_validation,
                probabilities,
            ),
            "ROC AUC": roc_auc_score(
                y_validation,
                probabilities,
            ),
        }

        comparison_results.append(result)

        print("\nValidation results:")
        for key, value in result.items():
            if isinstance(value, (float, np.floating)):
                print(f"{key}: {value:.4f}")
            else:
                print(f"{key}: {value}")

        if result["F1 Score"] > best_validation_f1:

            best_validation_f1 = result["F1 Score"]
            best_model_name = model_name
            best_threshold = threshold

    # Step 6: Save algorithm comparison
    comparison_df = pd.DataFrame(comparison_results)

    comparison_df = comparison_df.sort_values(
        by="F1 Score",
        ascending=False,
    )

    comparison_df.to_csv(
        OUTPUT_COMPARISON,
        index=False,
    )

    print("\nALGORITHM COMPARISON")
    print(comparison_df.to_string(index=False))

    print("\nSelected algorithm:", best_model_name)
    print(f"Selected threshold: {best_threshold:.2f}")

    # Step 7: Train final model on July to October.
    # Keep November separate for threshold analysis
    # and model explanation.
    best_model = create_model(best_model_name)

    best_model.fit(
        X_tuning,
        y_tuning,
    )

    # Step 8: Evaluate final model on December
    final_results = evaluate_model(
        best_model,
        X_test,
        y_test,
        best_threshold,
        "December Final Test",
    )

    final_results["Selected Algorithm"] = best_model_name

    # Step 9: Save model
    joblib.dump(
        best_model,
        OUTPUT_MODEL,
        compress=3,
    )

    print(f"\nBest model saved: {OUTPUT_MODEL}")

    # Step 10: Save threshold
    with open(
        OUTPUT_THRESHOLD,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(str(best_threshold))

    print(f"Threshold saved: {OUTPUT_THRESHOLD}")

    # Step 11: Save final results
    pd.DataFrame(
        [final_results]
    ).to_csv(
        OUTPUT_FINAL_RESULTS,
        index=False,
    )

    # Step 12: Analyze November thresholds
    threshold_model = create_model(best_model_name)

    threshold_model.fit(
        X_tuning,
        y_tuning,
    )

    validation_probabilities = threshold_model.predict_proba(
        X_validation
    )[:, 1]

    threshold_df = analyze_thresholds(
        y_validation,
        validation_probabilities,
    )

    threshold_df.to_csv(
        OUTPUT_THRESHOLD_ANALYSIS,
        index=False,
    )

    print("\nTHRESHOLD ANALYSIS")
    print(threshold_df.round(4).to_string(index=False))

    # Step 13: Permutation feature importance
    generate_permutation_importance(
        threshold_model,
        X_validation,
        y_validation,
        best_threshold,
    )

    # Step 14: Prediction error analysis
    analyze_prediction_errors(
        threshold_model,
        X_validation,
        y_validation,
        best_threshold,
    )

    # Step 15: Probability calibration
    analyze_probability_calibration(
        threshold_model,
        X_validation,
        y_validation,
    )

    print("\n" + "=" * 60)
    print("ALGORITHM COMPARISON COMPLETED")
    print("=" * 60)

    print("\nGenerated files:")

    for output_file in [
        OUTPUT_MODEL,
        OUTPUT_THRESHOLD,
        OUTPUT_COMPARISON,
        OUTPUT_FINAL_RESULTS,
        OUTPUT_THRESHOLD_ANALYSIS,
        OUTPUT_PERMUTATION_CSV,
        OUTPUT_PERMUTATION_PNG,
        OUTPUT_ERRORS_CSV,
        OUTPUT_CALIBRATION_CSV,
        OUTPUT_CALIBRATION_PNG,
    ]:
        print(output_file.name)


# ============================================================
# 14. PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
