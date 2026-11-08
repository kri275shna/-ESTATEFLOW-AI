from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.entities import Project, PropertyFact


def get_project_grounding_context(db: Session, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all active projects and their approved fact sheets from the database."""
    query = db.query(Project).filter(Project.is_active == True)
    if project_id:
        query = query.filter(Project.id == project_id)
    projects = query.all()

    context = []
    for p in projects:
        facts = db.query(PropertyFact).filter(
            PropertyFact.project_id == p.id,
            PropertyFact.is_public == True
        ).all()

        context.append({
            "project_id": p.id,
            "code": p.code,
            "name": p.name,
            "location": p.location,
            "rera_number": p.rera_number,
            "configurations": p.configurations,
            "price_range": f"₹{float(p.min_price)/100000:.0f} Lakh - ₹{float(p.max_price)/100000:.0f} Lakh",
            "possession_date": p.possession_date,
            "facts": [
                {
                    "id": f.id,
                    "category": f.category,
                    "attribute": f.attribute_name,
                    "content": f.approved_fact
                }
                for f in facts
            ]
        })
    return context


def retrieve_relevant_facts(
    db: Session,
    user_query: str,
    project_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Evaluates user query tokens against approved property facts in the database.
    Strict closed-world matching: only returns approved facts.
    """
    query_lower = user_query.lower()
    all_context = get_project_grounding_context(db, project_id)
    matched_facts = []

    keyword_categories = {
        "price": ["price", "cost", "budget", "rate", "lakh", "crore", "payment", "bhav", "kimat"],
        "carpet": ["carpet", "size", "sqft", "sq ft", "area", "dimension", "map"],
        "amenit": ["amenit", "club", "pool", "gym", "garden", "sports", "facility", "ev charging"],
        "rera": ["rera", "approval", "legal", "possession", "completion", "handover", "date", "year"],
        "locat": ["location", "shela", "sg highway", "bopal", "vaishno devi", "where", "connectivity", "distance", "road"]
    }

    for proj in all_context:
        for f in proj["facts"]:
            category_lower = f["category"].lower()
            attr_lower = f["attribute"].lower()
            fact_lower = f["content"].lower()

            # Direct word intersection or concept match
            for concept, keywords in keyword_categories.items():
                if any(kw in query_lower for kw in keywords):
                    if any(kw in category_lower or kw in attr_lower or kw in fact_lower for kw in keywords):
                        matched_facts.append({
                            "project_name": proj["name"],
                            "rera_number": proj["rera_number"],
                            "category": f["category"],
                            "attribute": f["attribute"],
                            "content": f["content"],
                            "fact_id": f["id"]
                        })

    # Deduplicate matched facts by fact_id
    unique_matches = []
    seen_ids = set()
    for m in matched_facts:
        if m["fact_id"] not in seen_ids:
            seen_ids.add(m["fact_id"])
            unique_matches.append(m)

    return unique_matches
