from socnhotv.social.models import (
    SocialAccount,
    Post,
    PostTarget,
    PostMedia,
    RecurringSlot,
    CalendarNote,
    PostingWindow,
    now_iso,
)


def test_social_account_defaults():
    acc = SocialAccount(
        platform="youtube",
        handle="@socnhotv",
        display_name="Sóc Nhỏ TV",
        posting_windows=[
            PostingWindow(weekday=0, start="19:00", end="21:00"),
            PostingWindow(weekday=2, start="19:00", end="21:00"),
        ],
    )
    assert acc.id.startswith("acc_")
    assert acc.platform == "youtube"
    assert acc.status == "manual"
    assert len(acc.posting_windows) == 2
    assert acc.daily_limit == 5


def test_post_and_target_creation():
    target = PostTarget(
        account_id="acc_yt_1",
        platform="youtube",
        title="Tập 1: Sóc Nhỏ",
        scheduled_at="2026-11-05T19:00:00+07:00",
        privacy="public",
    )
    post = Post(
        project_id="soc-nho-tv",
        title="Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
        media=[
            PostMedia(path="content/video.mp4", kind="video", duration_s=120.5)
        ],
        targets=[target],
    )
    assert post.id.startswith("post_")
    assert post.status == "draft"
    assert post.approval.required is True
    assert len(post.targets) == 1
    assert post.targets[0].platform == "youtube"
    assert "+07:00" in post.created_at


def test_recurring_slot_and_note():
    slot = RecurringSlot(
        account_id="acc_yt_1",
        rrule="FREQ=WEEKLY;BYDAY=MO,WE,FR;BYHOUR=19;BYMINUTE=0",
        label="Tối 19h T2-T4-T6",
    )
    assert slot.id.startswith("slot_")
    assert "FREQ=WEEKLY" in slot.rrule

    note = CalendarNote(date="2026-11-11", text="Sự kiện 11.11 Siêu Sale")
    assert note.id.startswith("note_")
    assert note.date == "2026-11-11"
