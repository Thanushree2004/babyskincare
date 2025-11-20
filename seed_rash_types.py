"""Seed detailed care & prevention tips for each rash type.
Run: python seed_rash_types.py
Requires app context.
"""
import json
from app import create_app
from extensions import db
from models import RashType

# Detailed structured tips: each entry includes home care, prevention, doctor consult triggers.
RASH_TIPS = {
    "Candidiases": {
        "home_care": {
            "en": [
                "Keep affected area clean and dry; gently pat after washing.",
                "Use mild, fragrance-free soap; avoid talc powders.",
                "Apply antifungal cream only if doctor prescribed previously."],
            "kn": [
                "ಬಾಧಿತ ಭಾಗವನ್ನು ಸ್ವಚ್ಛವಾಗಿ ಒಣಗಿಸಿ; ಒರೆಸಿ ಒಣವಾಗಿರಿಸಿ.",
                "ಸುಗಂಧರಹಿತ ಮೃದುವಾದ ಸಾಬೂನು ಬಳಸಿ; ಟಾಲ್ಕ್ ಪುಡಿ ತಪ್ಪಿಸಿ.",
                "ಹಿಂದೆ ವೈದ್ಯರು ಸೂಚಿಸಿದರೆ ಮಾತ್ರ ಎಂಟಿಫಂಗಲ್ ಕ್ರೀಂ ಹಚ್ಚಿ."],
        },
        "prevention": {
            "en": [
                "Change diapers every 2–3 hours or when wet.",
                "Give diaper‑free air time daily.",
                "Use breathable cotton clothing; avoid tight synthetics."],
            "kn": [
                "ಹಾಡನ್ನು 2–3 ಗಂಟೆಗೆ ಒಮ್ಮೆ ಅಥವಾ ಒದ್ದೆಯಾಗುತ್ತಿದ್ದಂತೆ ಬದಲಿಸಿ.",
                "ಪ್ರತಿದಿನ ಕೆಲವು ಸಮಯ ಡಯಪರ್ ಇಲ್ಲದೆ ಗಾಳಿಗೆ ಇರಿಸಿ.",
                "ಉಸಿರಾಡುವ ಹತ್ತಿ ಬಟ್ಟೆ ಬಳಸಿ; ಬಿಗಿಯಾದ ಸಿಂಥಟಿಕ್ ತಪ್ಪಿಸಿ."],
        },
        "doctor_if": {
            "en": ["Redness spreading with small satellite spots.", "No improvement in 3–4 days.", "Fever or unusual irritability."],
            "kn": ["ಕೆಂಪು ವಿಸ್ತಾರವಾಗಿ ಸಣ್ಣ ಚುಕ್ಕೆಗಳು ಕಾಣಿಸಿದರೆ.", "3–4 ದಿನಗಳಲ್ಲಿ ಸುಧಾರಣೆ ಆಗದಿದ್ದರೆ.", "ಜ್ವರ ಅಥವಾ ಅಸಹಜ ಕಿರಿಕಿರಿ ಇದ್ದರೆ."]
        }
    },
    "Chickenpox": {
        "home_care": {
            "en": ["Keep nails short to reduce scratching.", "Lukewarm oatmeal baths to soothe itching.", "Give plenty of fluids."],
            "kn": ["ಗರಿಗಳು ಚಿಕ್ಕದಾಗಿರಲಿ; ಕೊರೆಯುವುದು ಕಡಿಮೆಯಾಗುತ್ತದೆ.", "ಇಚ್ಚೆ ಕಡಿಮೆ ಮಾಡಲು ಉಷ್ಣತೆ ಕಡಿಮೆ ಓಟ್ಸ್ ಸ್ನಾನ.", "ಹೇರಳವಾದ ದ್ರವ ನೀಡಿರಿ."],
        },
        "prevention": {"en": ["Vaccination when age appropriate.", "Keep child isolated till lesions scab.", "Clean commonly touched surfaces."],
                        "kn": ["ವಯಸ್ಸಿಗೆ ತಕ್ಕಂತೆ ಲಸಿಕೆ ಹಾಕಿಸಿ.", "ಗಬ್ಬು ಬರುವವರೆಗೆ ಬೇರೆ ಮಕ್ಕಳಿಂದ ದೂರ ಇರಿಸಿ.", "ಮೆಚ್ಚಿನ ವಸ್ತುಗಳನ್ನು ಸ್ವಚ್ಛಗೊಳಿಸಿ."]},
        "doctor_if": {"en": ["Breathing problems or persistent high fever.", "Lesions become swollen with yellow pus.", "Signs of dehydration."],
                      "kn": ["ಶ್ವಾಸಕೋಶ ತೊಂದರೆ ಅಥವಾ ಉನ್ನತ ಜ್ವರ ಮುಂದುವರಿದರೆ.", "ಗಬ್ಬುಗಳು ಊದಿಕೊಂಡು ಹಳದಿ ಪು ಟ್ರಿಗರ್ ಆಗಿದರೆ.", "ದ್ರವ ಕ್ಷಯ ಲಕ್ಷಣಗಳು ಕಾಣಿಸಿದರೆ."]}
    },
    "HdMs": {
        "home_care": {"en": ["Moisturize frequently.", "Avoid overheating; light layers.", "Cleanse gently; pat dry."],
                       "kn": ["ಎಲ್ಲಾ ಸಮಯ ಮೃದು ಕ್ರೀಮ್ ಹಚ್ಚಿ.", "ಹೆಚ್ಚು ಬಿಸಿ ತಪ್ಪಿಸಿ; ತೆಳ್ಳನೆ ಪದರದ ಬಟ್ಟೆಗಳು.", "ಮೃದುವಾಗಿ ತೊಳೆಯಿರಿ; ನಾಜೂಕಾಗಿ ಒರೆಸಿ." ]},
        "prevention": {"en": ["Cool room temperature 22–24°C.", "Use cotton clothing.", "Do not over‑apply oils."],
                        "kn": ["ಕೊಠಡಿ ತಾಪಮಾನ ಶೀತ 22–24°C ಇರಲಿ.", "ಹತ್ತಿ ಬಟ್ಟೆ ಬಳಸಿರಿ.", "ಎಣ್ಣೆ ಹೆಚ್ಚು ಹಚ್ಚಬೇಡಿ."]},
        "doctor_if": {"en": ["Pain, oozing or infection signs.", "Fever or poor feeding."],
                      "kn": ["ನೋವು, ಹೊರಹರಿವು ಅಥವಾ ಸೋಂಕಿನ ಲಕ್ಷಣಗಳು.", "ಜ್ವರ ಅಥವಾ ತಿಂದುಕೊಳ್ಳದಿರುವುದು."]}
    },
    "Impetigo": {
        "home_care": {"en": ["Gently remove crusts with warm water.", "Keep nails short.", "Wash towels/clothes daily."],
                       "kn": ["ಬಿಸಿ ನೀರಿನಿಂದ ಮೃದುವಾಗಿ ಗರಿಗಳನ್ನು ತೆಗೆದುಹಾಕಿ.", "ಗರಿಗಳು ಚಿಕ್ಕದಿರಲಿ.", "ತೊವೆಗಳು ಮತ್ತು ಬಟ್ಟೆ ಪ್ರತಿದಿನ ತೊಳೆಯಿರಿ."]},
        "prevention": {"en": ["Hand hygiene after touching lesions.", "Do not share towels or clothing.", "Cover lesions loosely."],
                        "kn": ["ಗಬ್ಬು ಮುಟ್ಟಿದ ಮೇಲೆ ಕೈ ತೊಳೆಯಿರಿ.", "ತೊವೆಗಳು ಅಥವಾ ಬಟ್ಟೆ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ.", "ಗಬ್ಬನ್ನು ಸಡಿಲವಾಗಿ ಮುಚ್ಚಿರಿ."]},
        "doctor_if": {"en": ["Rapidly increasing lesions.", "Fever or swollen nodes.", "No improvement in 48h treatment."],
                      "kn": ["ತ್ವರಿತವಾಗಿ ಹೆಚ್ಚುತ್ತಿರುವ ಗಬ್ಬುಗಳು.", "ಜ್ವರ ಅಥವಾ ಊದಿಕೊಂಡ ಲಿಂಫ್ ಗ್ಲಾಂಡ್.", "48 ಗಂಟೆಯ ಚಿಕಿತ್ಸೆಯಲ್ಲಿ ಸುಧಾರಣೆ ಇಲ್ಲ."]}
    },
    "Ringworm": {
        "home_care": {"en": ["Keep area clean and dry.", "Separate towel; wash after use.", "Avoid tight clothing."],
                       "kn": ["ಪ್ರದೇಶ ಸ್ವಚ್ಛ ಹಾಗೂ ಒಣವಾಗಿರಲಿ.", "ಪ್ರತ್ಯೇಕ ತೊವೆ ಬಳಸಿ; ಬಳಕೆಯ ನಂತರ ತೊಳೆಯಿರಿ.", "ಬಿಗಿಯಾದ ಬಟ್ಟೆ ತಪ್ಪಿಸಿ."]},
        "prevention": {"en": ["Do not share hats or combs.", "Wash hands after pet contact.", "Dry skin folds quickly."],
                        "kn": ["ಟೊಪ್ಪಿ ಅಥವಾ ಕಾಂಬ್ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ.", "ಪಾಲು ಜೀವಿಯನ್ನು ಮುಟ್ಟಿದ ನಂತರ ಕೈ ತೊಳೆಯಿರಿ.", "ಚರ್ಮದ ಮಡಚುಗಳನ್ನು ಬೇಗ ಒಣಗಿಸಿ."]},
        "doctor_if": {"en": ["Lesion enlarges.", "Multiple circular lesions.", "Pus or pain."],
                      "kn": ["ಗಬ್ಬು ದೊಡ್ಡದಾಗಿದ್ರೆ.", "ಹಲವು ವೃತ್ತಾಕಾರದ ಗಬ್ಬುಗಳು.", "ಪು ಅಥವಾ ನೋವು." ]}
    },
    "diaper_rash": {
        "home_care": {"en": ["Change wet/soiled diapers promptly.", "Use thick zinc oxide barrier.", "Daily diaper‑free air time."],
                       "kn": ["ಒದ್ದೆ/ಕಳೆದುಹೋದ ಡಯಪರ್ ತಕ್ಷಣ ಬದಲಾಯಿಸಿ.", "ದಪ್ಪ ಜಿಂಕ್ ಆಕ್ಸೈಡ್ ಕ್ರಮ ಬಳಸಿ.", "ಪ್ರತಿದಿನ ಸ್ವಲ್ಪ ಸಮಯ ಡಯಪರ್ ಇಲ್ಲದೆ ಇರಿಸಿ."]},
        "prevention": {"en": ["Avoid alcohol/fragrance wipes.", "Use super absorbent diapers.", "Do not fasten too tightly."],
                        "kn": ["ಆಲ್ಕೊಹಾಲ್/ಸುವಾಸನೆ ಇರುವ ವೈಪ್ಸ್ ತಪ್ಪಿಸಿ.", "ಹೆಚ್ಚು ಶೋಷಕ ಡಯಪರ್ ಬಳಸಿ.", "ಅತಿಯಾದ ಬಿಗಿಯಾಗಿ ಕಟ್ಟಬೇಡಿ."]},
        "doctor_if": {"en": ["Open sores or pus.", "Rash >1 week or worsening.", "Fever or oral thrush."],
                      "kn": ["ತೆರೆದ ಗಾಯಗಳು ಅಥವಾ ಪು.", "1 ವಾರಕ್ಕಿಂತ ಹೆಚ್ಚು ಅಥವಾ ಕೆಟ್ಟದಾದರೆ.", "ಜ್ವರ ಅಥವಾ ಬಾಯಲ್ಲಿ ಬಿಳಿ ಜಾಗ." ]}
    },
    "eczema_rash": {
        "home_care": {"en": ["Moisturize 2–3 times daily.", "Short lukewarm baths then moisturize.", "Avoid harsh wool/detergents."],
                       "kn": ["ದಿನಕ್ಕೆ 2–3 ಬಾರಿ ತೇವ ಕ್ರೀಂ ಹಚ್ಚಿ.", "ಚಿಕ್ಕ ಉಷ್ಣ ಸ್ನಾನ ನಂತರ ತೇವ ನೀಡಿರಿ.", "ಕಟುವಾದ ಉಣ್ಣೆ / ಡಿಟರ್ಜಂಟ್ ತಪ್ಪಿಸಿ."]},
        "prevention": {"en": ["Use gentle dye‑free detergents.", "Maintain routine even when clear.", "Keep humidity 40–50%."],
                        "kn": ["ಬಣ್ಣರಹಿತ ಮೃದುವಾದ ಡಿಟರ್ಜಂಟ್ ಬಳಸಿ.", "ರಾಷ್ ಇಲ್ಲದಿದ್ದರೂ ಕ್ರಮ ಮುಂದುವರಿಸಿ.", "ಆರ್ದ್ರತೆ 40–50% ಇರಲಿ."]},
        "doctor_if": {"en": ["Yellow oozing or painful crusts.", "Sleep disturbed from itching.", "No improvement after 1 week care."],
                      "kn": ["ಹಳದಿ ಹೊರಹರಿವು ಅಥವಾ ನೋವಿನ ಗರಿಗಳು.", "ಕೆರಿಕೆ ಕಾರಣ ನಿದ್ದೆ ಭಂಗ.", "1 ವಾರದ ಆರೈಕೆಯ ನಂತರ ಸುಧಾರಣೆ ಇಲ್ಲ."]}
    },
    "healthy": {
        "home_care": {"en": ["Continue gentle bathing & moisturizing.", "Protect from strong sun."],
                       "kn": ["ಮೃದುವಾದ ಸ್ನಾನ ಮತ್ತು ತೇವ ಕ್ರಮ ಮುಂದುವರಿಸಿ.", "ತೀವ್ರ ಸೂರ್ಯನಿಂದ ರಕ್ಷಿಸಿರಿ."]},
        "prevention": {"en": ["Use mild fragrance‑free products.", "Keep baby hydrated.", "Breathable clothing & regular diaper change."],
                        "kn": ["ಮೃದುವಾದ ಸುವಾಸನೆ ರಹಿತ ಉತ್ಪನ್ನ ಬಳಸಿ.", "ಮಗುವಿಗೆ ಸಾಕಷ್ಟು ದ್ರವ.", "ಉಸಿರಾಡುವ ಬಟ್ಟೆ ಮತ್ತು ನಿಯಮಿತ ಡಯಪರ್ ಬದಲಾವಣೆ."]},
        "doctor_if": {"en": ["Sudden new rash.", "Cracking dryness.", "Pain or fever signs."],
                      "kn": ["ಹಠಾತ್ ಹೊಸ ರಾಶ್.", "ಒಡೆದ ಒಣತನ.", "ನೋವು ಅಥವಾ ಜ್ವರ ಲಕ್ಷಣಗಳು."]}
    },
    "heat_rash": {
        "home_care": {"en": ["Move to cooler ventilated area.", "Loose light clothing.", "Cool with lukewarm water."],
                       "kn": ["ತಂಪಾದ ಗಾಳಿಯ ಸ್ಥಳಕ್ಕೆ ಕ್ಷೇತ್ರಾಂತರಿಸಿ.", "ಸಡಿಲ ಹಗುರ ಬಟ್ಟೆ.", "ಮಚ್ಚನ್ನು ಉಷ್ಣ ಕಡಿಮೆ ನೀರಿನಿಂದ ತಂಪಾಗಿಸಿ."]},
        "prevention": {"en": ["Avoid overdressing.", "Comfortable room temperature not humid.", "Dry sweat quickly."],
                        "kn": ["ಹೆಚ್ಚಾಗಿ ಬಟ್ಟೆ ಹಾಕಬೇಡಿ.", "ಕಡಿಮೆ ಆರ್ದ್ರತೆ ತಾಪಮಾನ.", "ಬೆವರು ಬೇಗ ಒರೆಸಿ."]},
        "doctor_if": {"en": ["Rash >3 days or worse.", "Blisters, pus or spreading.", "Fever or unusual fussiness."],
                      "kn": ["3 ದಿನಕ್ಕೂ ಹೆಚ್ಚು ಅಥವಾ ಕೆಟ್ಟದಾದರೆ.", "ಗುಳ್ಳೆಗಳು, ಪು ಅಥವಾ ವ್ಯಾಪಕವಾಗುತ್ತದೆ.", "ಜ್ವರ ಅಥವಾ ಅಸಹಜ ಕಿರಿಕಿರಿ."]}
    }
}

def main():
    app = create_app()
    with app.app_context():
        for name, sections in RASH_TIPS.items():
            existing = RashType.query.filter_by(name=name).first()
            payload = json.dumps({
                "home_care": sections["home_care"],
                "prevention": sections["prevention"],
                "doctor_if": sections["doctor_if"]
            }, ensure_ascii=False)
            if existing:
                existing.care_tips = payload
            else:
                db.session.add(RashType(name=name, care_tips=payload))
        db.session.commit()
        print("Seeded/updated rash types.")

if __name__ == "__main__":
    main()
