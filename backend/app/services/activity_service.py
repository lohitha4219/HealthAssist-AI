from typing import Optional

from sqlalchemy.orm import Session

from app.models.health_activity import HealthActivity


def record_activity(
    db: Session,
    *,
    user_id: int,
    activity_type: str,
    title: str,
    description: Optional[str] = None,
    reference_id: Optional[str] = None,
    reference_type: Optional[str] = None,
) -> HealthActivity:
    activity = HealthActivity(
        user_id=user_id,
        activity_type=activity_type,
        title=title[:200],
        description=description,
        reference_id=reference_id,
        reference_type=reference_type,
    )
    db.add(activity)
    return activity
