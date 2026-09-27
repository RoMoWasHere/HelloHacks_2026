import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer

from housing_fraud_nlp import WarningSignFeatures

LISTINGS = pd.DataFrame({
    "title": ["Sunny 2BR near UBC", "Quiet 1BR in Kits"],
    "description": [
        "Lots of people are interested.\nSend a $500 deposit today to hold it.",
        "Deposit due at lease signing. Credit check required.",
    ],
})


def test_feature_names():
    names = WarningSignFeatures().get_feature_names_out()
    assert list(names[:5]) == [
        "deposit_demand", "personal_info_request", "etransfer_request",
        "high_demand_claim", "foreign_payment",
    ]
    assert len(names) == 10
    assert len(WarningSignFeatures(include_counts=False).get_feature_names_out()) == 5


def test_transform_title_and_description_columns():
    features = WarningSignFeatures().fit_transform(LISTINGS[["title", "description"]])
    frame = pd.DataFrame(features, columns=WarningSignFeatures().get_feature_names_out())
    assert frame.loc[0, "deposit_demand"] == 1
    assert frame.loc[0, "high_demand_claim"] == 1
    assert frame.loc[1].sum() == 0


def test_missing_text_is_treated_as_empty():
    frame = pd.DataFrame({"title": [None], "description": [np.nan]})
    assert WarningSignFeatures().fit_transform(frame).tolist() == [[0.0] * 10]


def test_works_inside_column_transformer_and_can_be_cloned():
    preprocess = ColumnTransformer([("warning_signs", WarningSignFeatures(), ["title", "description"])])
    output = clone(preprocess).fit_transform(LISTINGS)
    assert output.shape == (2, 10)
    assert list(preprocess.fit(LISTINGS).get_feature_names_out())[0] == "warning_signs__deposit_demand"
