from hifuel.review_pack import assign_codes, build_html, whatsapp_message


def _post(pid, date, time, **kw):
    base = {"id": pid, "date": date, "time": time, "account": "pathvik", "account_name": "Pathvik", "platform": "instagram",
            "format": "reel", "status": "draft", "approver": "founder", "hook": "Hook <b>", "caption": "Body", "cta": "",
            "hashtags": ["#Pathvik"], "thread_parts": [], "issues": [], "design_brief": {"slides": [], "reel": {"shots": [
                {"seconds": "0-2", "shot": "Phone", "on_screen_text": "Hi", "voiceover": ""}], "duration_seconds": 20}}}
    return {**base, **kw}


def test_codes_follow_date_and_time_order():
    posts = [_post("b", "2026-10-21", "09:00"), _post("a", "2026-10-20", "19:30"), _post("c", "2026-10-20", "09:30")]
    assert assign_codes(posts, "P") == {"c": "P01", "a": "P02", "b": "P03"}


def test_pack_escapes_text_and_uses_the_pack_codes():
    posts = [_post(f"id{i}", "2026-10-26", f"1{i}:00", internal_notes="[CONFIRM] handle") for i in range(8)]
    codes = assign_codes(posts, "W")
    page = build_html(posts, codes, "Week", "sub", "intro")
    assert "Hook &lt;b&gt;" in page and "Hook <b>" not in page
    assert "W07 CHANGE" in page and "P07" not in page
    assert "To confirm" in page
    msg = whatsapp_message("Week", posts, codes, "")
    assert "W01–W08" in msg and "*W07 OK*" in msg
