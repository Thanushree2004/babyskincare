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
        "home_care": [
            "Keep affected area clean and dry; gently pat after washing.",
            "Use mild, fragrance-free soap; avoid talc powders (can irritate).",
            "Apply pediatrician-approved antifungal cream if previously prescribed only."],
        "prevention": [
            "Change diapers frequently (every 2-3 hours or when wet).",
            "Air time: allow diaper-free periods to reduce moisture.",
            "Avoid tight synthetic clothing; choose breathable cotton."],
        "doctor_if": [
            "Spreading redness or satellite pustules appear.",
            "No improvement in 3-4 days of gentle care.",
            "Fever or baby seems unusually irritable."]
    },
    "Chickenpox": {
        "home_care": [
            "Keep nails trimmed to reduce scratching infection risk.",
            "Use lukewarm oatmeal baths for itch relief.",
            "Offer plenty of fluids to prevent dehydration."],
        "prevention": [
            "Vaccination (if age-appropriate per pediatric schedule).",
            "Isolate from non-immune children until all lesions scab.",
            "Disinfect commonly touched objects gently."],
        "doctor_if": [
            "Breathing difficulty, persistent high fever, or lethargy.",
            "Lesions become very red, swollen, or filled with yellow pus.",
            "Dehydration signs: fewer wet diapers, dry mouth."]
    },
    "HdMs": {
        "home_care": [
            "Keep skin moisturized with hypoallergenic lotion.",
            "Avoid overheating: dress in light breathable layers.",
            "Gently cleanse with lukewarm water; pat dry."],
        "prevention": [
            "Maintain cool ambient temperature (22–24°C).",
            "Use cotton clothing; avoid rough seams.",
            "Do not over-apply oils/lotions that occlude pores."],
        "doctor_if": [
            "Rash becomes painful or oozes.",
            "Signs of infection (yellow crusts, warmth, swelling).",
            "Baby develops fever or poor feeding."]
    },
    "Impetigo": {
        "home_care": [
            "Gently wash crusts with warm water; do not scrub.",
            "Keep fingernails short; prevent scratching and spread.",
            "Launder towels and clothes in hot water daily."],
        "prevention": [
            "Hand hygiene after touching lesions.",
            "Do not share towels, bedding, or clothing.",
            "Keep lesions covered loosely if possible."],
        "doctor_if": [
            "Multiple new lesions appear rapidly.",
            "Fever, swollen lymph nodes, or spreading redness.",
            "No improvement within 48 hours of prescribed treatment."]
    },
    "Ringworm": {
        "home_care": [
            "Keep area clean and dry; wash gently once daily.",
            "Use separate towel; launder after each use.",
            "Avoid tight clothing occluding rash area."],
        "prevention": [
            "Do not share hats, brushes, or bedding.",
            "Wash hands after pet contact; check pets for patches.",
            "Keep skin folds dry; change sweaty clothes quickly."],
        "doctor_if": [
            "Lesion enlarges despite care.",
            "Multiple circular lesions or scalp involvement.",
            "Signs of secondary infection (pus, pain, heat)."]
    },
    "diaper_rash": {
        "home_care": [
            "Change diapers promptly when wet or soiled.",
            "Use thick barrier cream (zinc oxide) each change.",
            "Allow diaper-free time several times daily."],
        "prevention": [
            "Avoid wipes with alcohol/fragrance; use warm water for severe flares.",
            "Choose super-absorbent diapers that wick moisture.",
            "Do not overtighten diaper (reduces airflow)."],
        "doctor_if": [
            "Open sores, bleeding, or pus.",
            "Rash lasts >1 week or worsens despite care.",
            "Fever or thrush signs (white patches in mouth)."]
    },
    "eczema_rash": {
        "home_care": [
            "Moisturize 2-3 times daily with fragrance-free cream.",
            "Short lukewarm baths (5-10 min) then immediate moisturization.",
            "Identify and reduce triggers (wool, harsh detergents)."],
        "prevention": [
            "Use gentle, dye-free detergents.",
            "Maintain regular moisturization routine even when clear.",
            "Keep room humidity moderate (40–50%)."],
        "doctor_if": [
            "Areas ooze yellow fluid or form painful crusts.",
            "Sleep significantly disturbed due to itching.",
            "No response to over-the-counter emollients in 1 week."]
    },
    "healthy": {
        "home_care": [
            "Continue gentle bathing and moisturizing routine.",
            "Protect skin from excessive sun (shade, clothing)."],
        "prevention": [
            "Use mild fragrance-free products.",
            "Maintain good hydration.",
            "Regular diaper changes and breathable clothing."],
        "doctor_if": [
            "New rash forms suddenly.",
            "Persistent dryness with cracking.",
            "Any signs of pain or fever."]
    },
    "heat_rash": {
        "home_care": [
            "Move baby to a cooler, ventilated area.",
            "Light loose clothing; avoid occlusive creams.",
            "Gently cool skin with lukewarm water (not ice)."],
        "prevention": [
            "Avoid overdressing; remove one layer if sweating.",
            "Keep room temperature comfortable and not humid.",
            "Promptly dry skin after bathing or sweating."],
        "doctor_if": [
            "Rash persists >3 days or worsens.",
            "Blisters, pus, or spreading redness appear.",
            "Baby shows fever or unusual fussiness."]
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
            })
            if existing:
                existing.care_tips = payload
            else:
                db.session.add(RashType(name=name, care_tips=payload))
        db.session.commit()
        print("Seeded/updated rash types.")

if __name__ == "__main__":
    main()
