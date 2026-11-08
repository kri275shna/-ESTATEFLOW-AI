from typing import Optional, Dict, Any, Tuple


def calculate_qualification_score(
    preferred_bhk: Optional[str],
    budget_min: Optional[float],
    budget_max: Optional[float],
    buying_timeline: Optional[str],
    has_site_visit_interest: bool = False,
    project_code: Optional[str] = None
) -> Tuple[int, bool, Dict[str, Any]]:
    """
    Transparent, documented business rules qualification scoring:
    - Budget matches approved project range: +25 pts
    - Configuration specified & available: +25 pts
    - Buying timeline indicates immediate intent (<1 mo: +25, 1-3 mo: +15, 3-6 mo: +5): max +25 pts
    - Expressed interest or booked site visit: +25 pts
    Total: 0 to 100.
    Score >= 70 qualifies lead as 'High Intent'.
    """
    score = 0
    breakdown = {}

    # 1. Configuration check (2 BHK or 3 BHK)
    if preferred_bhk and ("2 BHK" in preferred_bhk or "3 BHK" in preferred_bhk):
        score += 25
        breakdown["configuration"] = {"points": 25, "reason": f"Matches project availability ({preferred_bhk})"}
    else:
        breakdown["configuration"] = {"points": 0, "reason": "No configuration selected"}

    # 2. Budget check (Harmony Enclave: 65L-95L, Skyline Serenity: 85L-1.2Cr)
    b_min = budget_min or 0
    b_max = budget_max or b_min
    if b_max >= 6500000:
        score += 25
        breakdown["budget"] = {"points": 25, "reason": "Budget meets developer entry ticket price (>= ₹65 Lakh)"}
    elif b_max > 0:
        score += 5
        breakdown["budget"] = {"points": 5, "reason": "Budget below minimum project ticket (₹65 Lakh)"}
    else:
        breakdown["budget"] = {"points": 0, "reason": "Budget not specified"}

    # 3. Timeline check
    if buying_timeline:
        t_lower = buying_timeline.lower()
        if "immediate" in t_lower or "0-1" in t_lower or "now" in t_lower or "this month" in t_lower:
            score += 25
            breakdown["timeline"] = {"points": 25, "reason": "Immediate intent (0-1 month)"}
        elif "1-3" in t_lower or "soon" in t_lower:
            score += 15
            breakdown["timeline"] = {"points": 15, "reason": "Near-term intent (1-3 months)"}
        elif "3-6" in t_lower:
            score += 5
            breakdown["timeline"] = {"points": 5, "reason": "Mid-term exploratory (3-6 months)"}
        else:
            breakdown["timeline"] = {"points": 0, "reason": "Long-term (6+ months)"}
    else:
        breakdown["timeline"] = {"points": 0, "reason": "Timeline not specified"}

    # 4. Site visit interest
    if has_site_visit_interest:
        score += 25
        breakdown["site_visit_intent"] = {"points": 25, "reason": "Active site visit scheduled or requested"}
    else:
        breakdown["site_visit_intent"] = {"points": 0, "reason": "Site visit not yet scheduled"}

    is_qualified = score >= 70
    return score, is_qualified, breakdown
