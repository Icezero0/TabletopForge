from app.modules.feedback.constants import FeedbackPage, FeedbackStatus, FeedbackType
from app.modules.feedback.models import Feedback


async def test_feedback_model_stores_core_fields(factories) -> None:
    creator = await factories.create_user()
    feedback = Feedback(
        creator_id=creator.id,
        feedback_type=FeedbackType.BUG.value,
        page=FeedbackPage.ROOM.value,
        title="Room map does not sync",
        description="The room state looks stale.",
        status=FeedbackStatus.OPEN.value,
    )

    assert feedback.creator_id == creator.id
    assert feedback.feedback_type == "bug"
    assert feedback.page == "room"
    assert feedback.status == "open"
