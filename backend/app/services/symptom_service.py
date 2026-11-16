from typing import Dict, List, Optional, Tuple

from app.schemas.symptoms import PossibleCauseItem, SymptomCatalogItem
from app.services.ai_service import AIUnavailableError, LocalAIService

SYMPTOM_CATALOG: List[SymptomCatalogItem] = [
    SymptomCatalogItem(id="fever", name="Fever", category="General", is_red_flag=False),
    SymptomCatalogItem(id="fatigue", name="Fatigue / Low Energy", category="General", is_red_flag=False),
    SymptomCatalogItem(id="chills", name="Chills", category="General", is_red_flag=False),
    SymptomCatalogItem(id="night_sweats", name="Night Sweats", category="General", is_red_flag=False),
    SymptomCatalogItem(id="headache", name="Headache", category="Neurological", is_red_flag=False),
    SymptomCatalogItem(id="dizziness", name="Dizziness / Lightheadedness", category="Neurological", is_red_flag=False),
    SymptomCatalogItem(id="confusion", name="Sudden Confusion or Slurred Speech", category="Neurological", is_red_flag=True),
    SymptomCatalogItem(id="fainting", name="Fainting / Loss of Consciousness", category="Neurological", is_red_flag=True),
    SymptomCatalogItem(id="cough", name="Cough", category="Respiratory", is_red_flag=False),
    SymptomCatalogItem(id="sore_throat", name="Sore Throat", category="Respiratory", is_red_flag=False),
    SymptomCatalogItem(id="nasal_congestion", name="Nasal Congestion / Runny Nose", category="Respiratory", is_red_flag=False),
    SymptomCatalogItem(id="shortness_of_breath", name="Shortness of Breath", category="Respiratory", is_red_flag=True),
    SymptomCatalogItem(id="wheezing", name="Wheezing", category="Respiratory", is_red_flag=False),
    SymptomCatalogItem(id="chest_pain", name="Chest Pain or Pressure", category="Cardiovascular", is_red_flag=True),
    SymptomCatalogItem(id="palpitations", name="Rapid Heartbeat / Palpitations", category="Cardiovascular", is_red_flag=False),
    SymptomCatalogItem(id="ankle_swelling", name="Swelling in Legs or Ankles", category="Cardiovascular", is_red_flag=False),
    SymptomCatalogItem(id="nausea", name="Nausea", category="Digestive", is_red_flag=False),
    SymptomCatalogItem(id="vomiting", name="Persistent Vomiting", category="Digestive", is_red_flag=False),
    SymptomCatalogItem(id="diarrhea", name="Diarrhea", category="Digestive", is_red_flag=False),
    SymptomCatalogItem(id="abdominal_pain", name="Abdominal Pain / Cramping", category="Digestive", is_red_flag=False),
    SymptomCatalogItem(id="heartburn", name="Heartburn / Acid Reflux", category="Digestive", is_red_flag=False),
    SymptomCatalogItem(id="loss_of_appetite", name="Loss of Appetite", category="Digestive", is_red_flag=False),
    SymptomCatalogItem(id="muscle_aches", name="Muscle Aches", category="Musculoskeletal", is_red_flag=False),
    SymptomCatalogItem(id="joint_pain", name="Joint Pain or Stiffness", category="Musculoskeletal", is_red_flag=False),
    SymptomCatalogItem(id="back_pain", name="Back Pain", category="Musculoskeletal", is_red_flag=False),
    SymptomCatalogItem(id="rash", name="Skin Rash or Hives", category="Dermatological", is_red_flag=False),
    SymptomCatalogItem(id="itching", name="Itching", category="Dermatological", is_red_flag=False),
    SymptomCatalogItem(id="facial_swelling", name="Swelling of Face, Lips, or Throat", category="Allergic / Immune", is_red_flag=True),
    SymptomCatalogItem(id="sleep_disturbance", name="Difficulty Sleeping", category="General", is_red_flag=False),
    SymptomCatalogItem(id="anxiety_restlessness", name="Restlessness or Stress Tension", category="General", is_red_flag=False),
    SymptomCatalogItem(id="ear_pain", name="Ear Pain or Pressure", category="ENT", is_red_flag=False),
    SymptomCatalogItem(id="eye_redness", name="Eye Redness or Irritation", category="ENT", is_red_flag=False),
]

RED_FLAG_KEYWORDS = {
    "chest pain",
    "chest pressure",
    "shortness of breath",
    "difficulty breathing",
    "trouble breathing",
    "sudden confusion",
    "slurred speech",
    "fainting",
    "loss of consciousness",
    "swelling of face",
    "lips, or throat",
    "uncontrolled bleeding",
    "severe allergic",
    "stiff neck",
}

CATEGORY_CAUSE_KNOWLEDGE: Dict[str, PossibleCauseItem] = {
    "Respiratory": PossibleCauseItem(
        title="Upper Respiratory or Airway Irritation",
        description=(
            "Viral respiratory infections, seasonal allergies, or dry/irritated airways commonly "
            "produce symptoms like cough, sore throat, or nasal congestion."
        ),
        category="Respiratory",
    ),
    "General": PossibleCauseItem(
        title="Systemic Immune Response, Rest Deficit, or Dehydration",
        description=(
            "Mild infections, sleep disruption, stress, or inadequate hydration often cause "
            "fatigue, feverishness, or general body tiredness."
        ),
        category="General",
    ),
    "Digestive": PossibleCauseItem(
        title="Gastrointestinal Irritation or Dietary Factors",
        description=(
            "Mild viral gastroenteritis, food intolerances, acid reflux, or temporary digestive "
            "upset are frequent general contributors to stomach discomfort or nausea."
        ),
        category="Digestive",
    ),
    "Neurological": PossibleCauseItem(
        title="Tension, Hydration Changes, or Inner-Ear/Blood-Pressure Shifts",
        description=(
            "Tension headaches, dehydration, eye strain, or transient blood-pressure changes "
            "can contribute to headaches or mild lightheadedness."
        ),
        category="Neurological",
    ),
    "Musculoskeletal": PossibleCauseItem(
        title="Physical Strain, Posture, or Viral Myalgia",
        description=(
            "Muscle overuse, ergonomic strain, mild sprains, or generalized viral illness "
            "often trigger temporary muscle or joint soreness."
        ),
        category="Musculoskeletal",
    ),
    "Cardiovascular": PossibleCauseItem(
        title="Circulatory Strain, Stress, or Fluid Balance Factors",
        description=(
            "Stress, caffeine, dehydration, or underlying cardiovascular factors can influence "
            "heart rhythm awareness or fluid retention and merit clinician evaluation."
        ),
        category="Cardiovascular",
    ),
    "Dermatological": PossibleCauseItem(
        title="Contact Sensitivity or Mild Inflammatory Skin Reaction",
        description=(
            "New soaps, detergents, seasonal dryness, or mild allergic sensitivity commonly "
            "present with localized rash or itching."
        ),
        category="Dermatological",
    ),
    "ENT": PossibleCauseItem(
        title="Sinus Pressure, Allergy, or Mild Surface Irritation",
        description=(
            "Eustachian tube congestion, seasonal pollen, or dry air frequently underlie "
            "mild ear pressure or eye irritation."
        ),
        category="ENT",
    ),
}


def _match_categories(symptoms: List[str]) -> Tuple[List[str], bool]:
    catalog_by_name = {item.name.lower(): item for item in SYMPTOM_CATALOG}
    categories: List[str] = []
    has_red_flag = False

    for sym in symptoms:
        lower = sym.lower()
        if lower in catalog_by_name:
            item = catalog_by_name[lower]
            if item.category not in categories:
                categories.append(item.category)
            if item.is_red_flag:
                has_red_flag = True
        for kw in RED_FLAG_KEYWORDS:
            if kw in lower:
                has_red_flag = True

        # Keyword-based category matching for custom symptom strings
        if any(w in lower for w in ("cough", "throat", "breath", "sinus", "congestion", "wheez")):
            if "Respiratory" not in categories:
                categories.append("Respiratory")
        elif any(w in lower for w in ("stomach", "nausea", "vomit", "diarrhea", "abdom", "reflux", "appetite")):
            if "Digestive" not in categories:
                categories.append("Digestive")
        elif any(w in lower for w in ("head", "dizz", "confus", "speech", "faint", "migraine")):
            if "Neurological" not in categories:
                categories.append("Neurological")
        elif any(w in lower for w in ("chest", "heart", "palpit", "swelling")):
            if "Cardiovascular" not in categories:
                categories.append("Cardiovascular")
        elif any(w in lower for w in ("muscle", "joint", "back")):
            if "Musculoskeletal" not in categories:
                categories.append("Musculoskeletal")
        elif any(w in lower for w in ("rash", "itch", "hive")):
            if "Dermatological" not in categories:
                categories.append("Dermatological")
        elif "General" not in categories:
            categories.append("General")

    if not categories:
        categories.append("General")

    return categories, has_red_flag


async def evaluate_symptoms(
    *,
    symptoms: List[str],
    duration: str,
    severity: str,
    additional_details: Optional[str],
    ai_service: Optional[LocalAIService] = None,
) -> dict:
    categories, has_red_flag = _match_categories(symptoms)

    details_lower = (additional_details or "").lower()
    if any(kw in details_lower for kw in RED_FLAG_KEYWORDS):
        has_red_flag = True

    if has_red_flag:
        urgency_level = "urgent_emergency"
        emergency_warning = (
            "One or more reported symptoms (such as chest pain, breathing difficulty, sudden neurological "
            "changes, fainting, or facial/throat swelling) can indicate an urgent medical condition. "
            "Seek immediate emergency medical care or contact local emergency services right away."
        )
    elif severity == "severe" or duration in {"1-2 weeks", "> 2 weeks"}:
        urgency_level = "prompt_care"
        emergency_warning = (
            "Because symptoms are marked as severe or persistent, consider scheduling a prompt "
            "evaluation with a licensed healthcare professional."
        )
    else:
        urgency_level = "routine"
        emergency_warning = None

    possible_causes = [
        CATEGORY_CAUSE_KNOWLEDGE.get(cat, CATEGORY_CAUSE_KNOWLEDGE["General"]).model_dump()
        for cat in categories[:4]
    ]

    care_guidance = [
        "Monitor symptom progression, temperature, hydration, and rest patterns over the next 24–48 hours.",
        "Avoid self-medicating with unfamiliar prescription drugs; verify over-the-counter options with a pharmacist or clinician.",
        "Contact a primary care clinician if symptoms worsen, fail to improve, or interfere with daily sleep, eating, or hydration.",
        "Seek immediate urgent or emergency care if you develop chest pain, severe shortness of breath, confusion, fainting, or high persistent fever.",
    ]

    sym_list_str = ", ".join(symptoms)
    educational_summary = (
        f"You logged {len(symptoms)} symptom(s) ({sym_list_str}) with {severity} severity "
        f"lasting {duration}. Based on educational health triage principles, these symptoms "
        f"primarily align with {', '.join(categories)} considerations. "
    )
    if has_red_flag:
        educational_summary += (
            "Because warning symptoms were included, prompt in-person emergency or urgent clinical evaluation is strongly advised."
        )
    else:
        educational_summary += (
            "Many mild-to-moderate symptoms improve with supportive rest and hydration, though persistent or worsening symptoms should be reviewed by a healthcare professional."
        )

    ai_enhanced = False
    if ai_service is not None:
        try:
            health = await ai_service.get_health()
            if health.available:
                prompt = (
                    f"Provide a concise 3-sentence educational health overview (NOT a diagnosis or prescription) "
                    f"for an adult reporting: {sym_list_str}; duration: {duration}; severity: {severity}. "
                    f"Context notes: {additional_details or 'None'}. "
                    f"Mention general wellness context and when to consult a clinician."
                )
                reply = await ai_service.generate_chat_reply(
                    messages=[{"role": "user", "content": prompt}],
                    system_prompt=(
                        "You are an educational healthcare information assistant. Never diagnose diseases "
                        "or prescribe treatments. Keep guidance calm, clear, and concise."
                    ),
                )
                if reply.content:
                    educational_summary = reply.content
                    ai_enhanced = True
        except AIUnavailableError:
            ai_enhanced = False
        except Exception:
            ai_enhanced = False

    return {
        "urgency_level": urgency_level,
        "educational_summary": educational_summary,
        "possible_causes": possible_causes,
        "care_guidance": care_guidance,
        "emergency_warning": emergency_warning,
        "ai_enhanced": ai_enhanced,
    }
