import re
from typing import Any, Dict, List, Optional

from app.services.ai_service import AIUnavailableError, LocalAIService

DISCLAIMER = (
    "Educational report parsing only — not a medical diagnosis. Extracted values reflect "
    "only what appeared in the uploaded document; missing reference ranges are never assumed. "
    "Review all laboratory results with a qualified physician."
)

# Matches patterns like:
#   Hemoglobin        14.2   g/dL    12.0 - 16.0
#   Fasting Glucose:  118    mg/dL   (70 - 99)
#   TSH               2.4    mIU/L   [0.4 - 4.0]
LAB_LINE_RE = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9\s/().,%-]{1,55}?)"
    r"(?::|\s{2,}|\s+)"
    r"(?P<value>-?\d+(?:\.\d+)?)\s*"
    r"(?P<unit>[A-Za-z%/µμ\^0-9]+(?:/[A-Za-z0-9]+)?)?"
    r"(?:\s*[\(\[]?\s*(?P<low>\d+(?:\.\d+)?)\s*[-–to]+\s*(?P<high>\d+(?:\.\d+)?)\s*[\)\]]?)?$"
)

NON_LAB_PREFIXES = ("page ", "date", "dob", "age", "id", "phone", "tel", "fax", "zip", "pincode")


def parse_lab_findings(extracted_text: Optional[str]) -> List[Dict[str, Any]]:
    if not extracted_text or not extracted_text.strip():
        return []

    findings: List[Dict[str, Any]] = []
    seen_names = set()

    for raw_line in extracted_text.splitlines():
        line = " ".join(raw_line.strip().split())
        if len(line) < 5 or len(line) > 160:
            continue
        if line.startswith("---"):
            continue
        lower = line.lower()
        if any(lower.startswith(prefix) for prefix in NON_LAB_PREFIXES):
            continue

        match = LAB_LINE_RE.match(line)
        if not match:
            continue

        name = match.group("name").strip(" :-")
        if len(name) < 2 or name.isdigit() or name.lower() in seen_names:
            continue

        try:
            val = float(match.group("value"))
        except ValueError:
            continue

        unit = (match.group("unit") or "").strip() or None
        low_raw = match.group("low")
        high_raw = match.group("high")

        ref_range: Optional[str] = None
        flag = "range_not_supplied"
        explanation = (
            f"Observed value {val}{f' {unit}' if unit else ''} extracted from document; "
            "no reference range was supplied on this line."
        )

        if low_raw is not None and high_raw is not None:
            low = float(low_raw)
            high = float(high_raw)
            if low <= high:
                ref_range = f"{low_raw} - {high_raw}"
                if val < low:
                    flag = "low"
                    explanation = (
                        f"Observed value ({val}{f' {unit}' if unit else ''}) is below the "
                        f"document-supplied range ({ref_range}). Discuss with your clinician."
                    )
                elif val > high:
                    flag = "high"
                    explanation = (
                        f"Observed value ({val}{f' {unit}' if unit else ''}) is above the "
                        f"document-supplied range ({ref_range}). Discuss with your clinician."
                    )
                else:
                    flag = "normal"
                    explanation = (
                        f"Observed value ({val}{f' {unit}' if unit else ''}) falls within the "
                        f"document-supplied range ({ref_range})."
                    )

        seen_names.add(name.lower())
        findings.append(
            {
                "test_name": name,
                "observed_value": val,
                "unit": unit,
                "reference_range": ref_range,
                "status": flag,
                "explanation": explanation,
            }
        )
        if len(findings) >= 40:
            break

    return findings


async def analyze_medical_report(
    *,
    filename: str,
    processing_status: str,
    extracted_text: Optional[str],
    ai_service: Optional[LocalAIService] = None,
) -> Dict[str, Any]:
    if not extracted_text or not extracted_text.strip():
        if processing_status == "scanned_no_text":
            summary = (
                "No embedded machine-readable text was found in this PDF (it may be a scanned image). "
                "The original file is securely stored; no lab values were invented."
            )
        elif processing_status == "image_stored":
            summary = (
                "Image report validated and securely stored. Automated numeric parsing applies only "
                "to text-readable PDFs; share this file with your doctor during consultation if needed."
            )
        else:
            summary = "File stored securely without extractable laboratory text."

        return {
            "summary": summary,
            "analysis": {
                "parsed_count": 0,
                "out_of_range_count": 0,
                "findings": [],
                "out_of_range": [],
                "ai_generated_summary": False,
                "disclaimer": DISCLAIMER,
            },
        }

    findings = parse_lab_findings(extracted_text)
    out_of_range = [f for f in findings if f["status"] in {"low", "high"}]

    if findings:
        summary = (
            f"Extracted {len(findings)} structured measurement(s) from '{filename}'. "
            f"{len(out_of_range)} value(s) fell outside the document-supplied reference range(s)."
        )
    else:
        summary = (
            f"Extracted readable text from '{filename}', though no standardized numeric lab "
            "table rows were matched automatically."
        )

    ai_generated = False
    if ai_service is not None:
        try:
            health = await ai_service.get_health()
            if health.available:
                snippet = extracted_text[:3000]
                prompt = (
                    "Provide a brief, plain-language educational summary of the following extracted "
                    "medical report text. Only reference numbers/terms explicitly present in the text; "
                    "never invent missing lab values or ranges, and do not diagnose or prescribe:\n\n"
                    f"{snippet}"
                )
                reply = await ai_service.generate_chat_reply(
                    messages=[{"role": "user", "content": prompt}],
                    system_prompt=(
                        "You are an educational healthcare report helper. Summarize only facts explicitly "
                        "present in the supplied text and advise discussing results with a physician."
                    ),
                )
                if reply.content:
                    summary = reply.content
                    ai_generated = True
        except (AIUnavailableError, Exception):
            ai_generated = False

    return {
        "summary": summary,
        "analysis": {
            "parsed_count": len(findings),
            "out_of_range_count": len(out_of_range),
            "findings": findings,
            "out_of_range": out_of_range,
            "ai_generated_summary": ai_generated,
            "disclaimer": DISCLAIMER,
        },
    }
