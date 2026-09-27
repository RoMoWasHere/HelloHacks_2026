# housing-fraud-nlp

Rule-based spaCy detectors that find textual rental-fraud warning signs in a
listing, based on the RCMP BC guidance on
[rental scams](https://rcmp.ca/en/bc/safety-tips/frauds-and-scams/rental-scams).

This module only extracts signals. It does not score or classify listings; the
larger project combines these signals as features.

## Setup

```sh
cd housing-fraud-nlp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest
```

`requirements.txt` installs spaCy, the `en_core_web_sm` model and pytest. Everything runs locally.

## Usage

```python
from housing_fraud_nlp import (
    detect_deposit_demand,
    detect_personal_information_request,
    detect_etransfer_request,
    detect_high_demand_claim,
    detect_foreign_payment_destination,
)

text = "Send the deposit by e-transfer to my brother in Mexico."

result = detect_deposit_demand(text)
result.detected   # True
result.evidence   # ["Send the deposit by e-transfer to my brother in Mexico."]
result.as_dict()  # {"detected": True, "evidence": [...]}
```

Each detector is independent, returns a `DetectionResult(detected, evidence)`,
and reports every triggering sentence as evidence. Parsing is cached, so running
all five on the same text parses it only once. `None` or empty text returns no
detection; any other non-string raises `TypeError`.

| Detector | Fires on | Does not fire on |
|---|---|---|
| `detect_deposit_demand` | "Send a $500 deposit to hold the apartment." | "A $500 deposit is required when signing the lease." |
| `detect_personal_information_request` | "Send me a photo of your driver's licence." | "You will need government ID when you sign the lease." |
| `detect_etransfer_request` | "Please send the deposit by e-transfer." | "Rent can be paid by e-transfer." |
| `detect_high_demand_claim` | "I already have several applicants." | "The apartment is available immediately." |
| `detect_foreign_payment_destination` | "Send the deposit to my brother in Mexico." | "I grew up in Mexico but now live in Vancouver." |

## How it works

- `patterns.py`: all vocabulary and `Matcher` token patterns. Extend detection here.
- `nlp.py`: loads `en_core_web_sm` once, adds a component that starts a new
  sentence at every line break, and caches parses.
- `detectors.py`: the five detectors plus shared helpers.

spaCy techniques used:
- **`Matcher` token patterns**: lemmas, lowercase forms and optional tokens, to
  handle variants like `e-transfer` / `e transfer` / `etransfer` / `Interac e-Transfer`.
- **`PhraseMatcher`**: a country gazetteer, with a case-sensitive version for
  abbreviations so the pronoun "us" never counts as the US.
- **Part-of-speech tags and dependency parsing**: to tell a request ("Send the
  deposit", "you need to pay", "I need your SIN") from a description ("the deposit
  is due at signing", "you will need ID"), and to check whether a country is
  attached to the payment or its recipient.
- **Named-entity recognition**: `GPE`/`LOC` for places and `MONEY` for amounts.
- **A custom pipeline component**: sentence boundaries at line breaks.

## Known limitations

- **Rules, not understanding.** Unusual phrasing, heavy slang, sarcasm and
  non-English text can be missed. Add patterns to `patterns.py` as new cases appear.
- **Sentence scope.** Each signal must appear within one sentence. A deposit
  request split across two sentences ("I'll hold it for you. Just send $500.")
  is not linked.
- **Request vs. description is imperfect.** `en_core_web_sm` sometimes mis-tags
  words (for example, it tags "e-transfer" as a noun), so there are fallbacks
  based on word position. Paying at lease signing or move-in is treated as normal
  unless the sentence also asks to hold the unit or adds urgency.
- **Payment-method mentions are not requests.** "Rent can be paid by e-transfer"
  and "E-transfer only" do not fire, even though the larger system may still want
  them as weaker features.
- **Foreign places depend on the gazetteer.** A country must be in
  `FOREIGN_PLACES` (NER finds places but does not know which are foreign). A
  foreign place tied to any recipient in a sentence about money counts, so
  "My sister in France loved it; pay the deposit to me" is a false positive.
- **High demand vs. marketing.** Phrases like "won't last" also appear in honest
  listings. Scarcity phrases describing amenities ("first come first served
  parking") are excluded, but other honest uses are not.
- **Cannot see the whole scam.** Evidence comes only from listing text. Photos,
  prices, and whether the landlord meets in person are out of scope.
