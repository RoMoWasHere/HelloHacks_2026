import pytest

from housing_fraud_nlp import (
    DetectionResult,
    detect_deposit_demand,
    detect_etransfer_request,
    detect_foreign_payment_destination,
    detect_high_demand_claim,
    detect_personal_information_request,
)

ALL_DETECTORS = [
    detect_deposit_demand,
    detect_personal_information_request,
    detect_etransfer_request,
    detect_high_demand_claim,
    detect_foreign_payment_destination,
]


# ---------------------------------------------------------------------------
# Deposit demand
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "Send a $500 deposit to reserve the apartment.",
    "Please e-transfer the deposit to reserve the unit.",
    "You need to send the security deposit before I remove the listing.",
    "Pay the deposit today and I'll hold the apartment for you.",
    "First month's rent and deposit must be sent to secure the property.",
    "SEND A $500 DEPOSIT TO HOLD THE APARTMENT!!!",
    "Once you send the deposit I will hold the unit for you",
    "Tons of inquiries already, so e-transfer $300 tonight to lock it in.",
])
def test_deposit_demand_detected(text):
    result = detect_deposit_demand(text)
    assert result.detected
    assert result.evidence == [text.strip()]


@pytest.mark.parametrize("text", [
    "A $500 security deposit is required when signing the lease.",
    "A $500 security deposit is required when you sign the lease.",
    "Please pay the deposit when you sign the lease.",
    "Security deposit: half of one month's rent.",
    "Deposits: half months rent",
    "Rent is $2,000 per month, utilities included.",
    "I will e-transfer you the deposit refund when you move out.",
])
def test_deposit_mention_without_demand_not_detected(text):
    assert not detect_deposit_demand(text).detected


# ---------------------------------------------------------------------------
# Personal information request
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "Please send me a photo of your driver's licence.",
    "I need your SIN before I can approve you.",
    "Please send your passport and banking information.",
    "Email me your ID and date of birth.",
    "please SEND me your Drivers License",
    "You must provide your bank account number to apply.",
])
def test_personal_information_request_detected(text):
    assert detect_personal_information_request(text).detected


@pytest.mark.parametrize("text", [
    "You will need government ID when you sign the lease.",
    "Government ID will be required when signing the lease.",
    "Please bring photo ID to the viewing.",
    "We will never ask for your SIN.",
    "Do not send your passport to anyone.",
    "The building is close to a bank and a passport office.",
])
def test_personal_information_mention_not_detected(text):
    assert not detect_personal_information_request(text).detected


# ---------------------------------------------------------------------------
# E-transfer request
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "Please send the deposit by e-transfer.",
    "Please Interac the money to me.",
    "You can transfer the funds to this email.",
    "Send me an Interac e-Transfer.",
    "Please transfer the $1,000 deposit.",
    "please send the deposit by E Transfer",
    "Etransfer the deposit to me asap",
    "Tons of inquiries already, so e-transfer $300 tonight.",
    "Kindly wire the first month's rent to my account.",
])
def test_etransfer_request_detected(text):
    assert detect_etransfer_request(text).detected


@pytest.mark.parametrize("text", [
    "The property has a transfer station nearby.",
    "Rent can be paid by e-transfer or cheque.",
    "I will transfer the keys to you at move-in.",
    "Bus transfers are easy from the Commercial-Broadway station.",
    "I will e-transfer you the deposit refund when you move out.",
    "Payment by e-transfer the day you move in.",
    "The unit is wired for high speed internet.",
])
def test_etransfer_without_request_not_detected(text):
    assert not detect_etransfer_request(text).detected


# ---------------------------------------------------------------------------
# High-demand claim
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "I already have several people interested, so you'll need to act quickly.",
    "Lots of people are interested.",
    "I already have several applicants.",
    "I have multiple offers.",
    "First person to send the deposit gets it.",
    "This won't be available for long.",
    "I've received tons of messages.",
    "Several people are ready to take it.",
    "FIRST COME, FIRST SERVED!",
])
def test_high_demand_claim_detected(text):
    assert detect_high_demand_claim(text).detected


@pytest.mark.parametrize("text", [
    "The apartment is available starting October 1.",
    "The apartment is available immediately.",
    "There are no other applicants yet.",
    "Other tenants in the building are quiet, friendly professional people.",
    "There is a first come first served outdoor parking lot for the building.",
])
def test_ordinary_availability_not_detected(text):
    assert not detect_high_demand_claim(text).detected


# ---------------------------------------------------------------------------
# Foreign payment destination
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "Please send the deposit to my brother in Mexico.",
    "Please transfer the money to my account in the UK.",
    "The payment needs to go to my friend in France.",
    "My assistant in the Philippines handles the payments.",
    "I live in France, so please e-transfer the deposit to me.",
    "I am overseas so send the deposit by Western Union.",
])
def test_foreign_payment_destination_detected(text):
    assert detect_foreign_payment_destination(text).detected


@pytest.mark.parametrize("text", [
    "I grew up in Mexico but now live in Vancouver.",
    "I currently live in Canada but I grew up in Mexico.",
    "The landlord is originally from Mexico.",
    "Send the deposit to my brother in Burnaby.",
    "Rent is $2000 and my family is from India.",
    "Please send the deposit to us.",
])
def test_country_mention_without_payment_link_not_detected(text):
    assert not detect_foreign_payment_destination(text).detected


# ---------------------------------------------------------------------------
# Behaviour shared by all detectors
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("detector", ALL_DETECTORS)
@pytest.mark.parametrize("text", ["", "   \n  ", None])
def test_empty_or_missing_text_returns_no_detection(detector, text):
    result = detector(text)
    assert result == DetectionResult(detected=False, evidence=[])


@pytest.mark.parametrize("detector", ALL_DETECTORS)
def test_non_string_input_raises_type_error(detector):
    with pytest.raises(TypeError):
        detector(12345)


@pytest.mark.parametrize("detector", ALL_DETECTORS)
def test_benign_listing_triggers_nothing(detector):
    listing = (
        "Bright 2 bedroom suite in Kitsilano, $2,650/month.\n"
        "Security deposit is half a month's rent, due at lease signing.\n"
        "Credit check and references required. Government ID required at signing.\n"
        "Please message me to book a viewing."
    )
    assert not detector(listing).detected


def test_one_sentence_triggers_three_independent_detectors():
    text = "Send the deposit by e-transfer to my brother in Mexico."
    assert detect_deposit_demand(text).detected
    assert detect_etransfer_request(text).detected
    assert detect_foreign_payment_destination(text).detected
    assert not detect_personal_information_request(text).detected
    assert not detect_high_demand_claim(text).detected


def test_multiple_evidence_sentences_are_all_returned():
    listing = (
        "Lovely one bedroom downtown.\n"
        "Lots of people are interested in this unit.\n"
        "No pets please.\n"
        "This won't last long, so message me today."
    )
    result = detect_high_demand_claim(listing)
    assert result.evidence == [
        "Lots of people are interested in this unit.",
        "This won't last long, so message me today.",
    ]


def test_scam_listing_triggers_every_detector():
    listing = (
        "Beautiful furnished 2BR in Kitsilano for $1,300.\n"
        "I am working overseas in Dubai so I cannot show the unit.\n"
        "I have multiple applicants, so send a $500 deposit today to hold it.\n"
        "Please e-transfer the money to my agent in Dubai.\n"
        "Also email me a photo of your driver's licence and your SIN."
    )
    for detector in ALL_DETECTORS:
        assert detector(listing).detected, detector.__name__


def test_result_as_dict():
    result = detect_deposit_demand("Send a $500 deposit to hold the apartment.")
    assert result.as_dict() == {
        "detected": True,
        "evidence": ["Send a $500 deposit to hold the apartment."],
    }
