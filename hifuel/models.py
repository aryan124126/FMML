"""Shapes of the data Claude returns. These double as the structured-output schema."""

from typing import Literal

from pydantic import BaseModel, Field

Platform = Literal["instagram", "linkedin", "facebook", "whatsapp_channel", "x"]
Theme = Literal[
    "educational",
    "impact_story",
    "initiative_promo",
    "behind_the_scenes",
    "founder_team_voice",
    "engagement",
]
PostFormat = Literal[
    "text", "single_image", "carousel", "reel", "story", "document", "poll", "channel_message", "thread"
]
# "shell" = a brief created on the hub (Quick Draft / Convert to Draft) that Claude has not written yet.
STATUSES = ["shell", "draft", "needs_changes", "approved", "scheduled", "posted", "rejected"]


class Slide(BaseModel):
    number: int
    text: str = Field(description="Exact text that appears on the slide")
    visual: str = Field(description="What the slide shows")


class Shot(BaseModel):
    seconds: str = Field(description="Time range, e.g. 0-2")
    shot: str = Field(description="What the camera shows")
    on_screen_text: str
    voiceover: str


class ReelScript(BaseModel):
    duration_seconds: int = Field(description="0 if the post is not a Reel")
    opening_hook: str = Field(description="What viewers see/hear in the first 1-2 seconds")
    shots: list[Shot]


class DesignBrief(BaseModel):
    format_notes: str
    slides: list[Slide] = Field(description="Carousel/document slides; empty if not a carousel")
    reel: ReelScript
    layout_notes: str
    colours: list[str] = Field(description="Hex colours from the account's brand")
    image_prompt: str = Field(description="Prompt for AI imagery, or empty if none is used")


class ClaimNote(BaseModel):
    claim: str = Field(description="The statistic or factual claim as written in the post")
    source: str = Field(description="Where it comes from (publication, URL or 'account config')")
    year: str


class PostDraft(BaseModel):
    idea_id: str = Field(description="Short slug shared by all versions of the same idea")
    account: str = Field(description="Account id from the config")
    platform: Platform
    date: str = Field(description="YYYY-MM-DD within the planning period")
    theme: Theme
    pillar: str
    format: PostFormat
    hook: str = Field(description="The first line; must stop the scroll")
    caption: str = Field(description="Body text after the hook, without hashtags or CTA")
    cta: str = Field(description="Call to action, or empty")
    hashtags: list[str]
    alt_text: str = Field(description="Alt text for the image/first slide, or empty for text posts")
    thread_parts: list[str] = Field(description="For X threads only: each part <= 280 chars; else empty")
    personalise_prompt: str = Field(
        description="Advocacy posts for people only: what the person should add in their own words; else empty"
    )
    design_brief: DesignBrief
    claims_notes: list[ClaimNote] = Field(description="Source and year for every statistic or claim")
    uses_ai_media: bool = Field(description="True if any image/video/voice of real people is AI-generated or edited")
    shows_children: bool = Field(description="True if the visual or text identifies or shows children")
    collab_with: str = Field(description="Instagram Collab partner account id, or empty")
    key_date: str = Field(description="Name of the festival/day this post ties to, or empty")
    internal_notes: str = Field(description="Notes for the reviewer: assumptions, things to confirm")


class WeekPlan(BaseModel):
    summary: str = Field(description="2-4 sentences: the plan's focus and theme mix")
    posts: list[PostDraft]
    questions_for_team: list[str] = Field(description="Open questions that block or weaken posts")


def publish_text(post: dict) -> str:
    """The text a person would paste into the platform (hook, body, CTA, hashtags)."""
    parts = [post.get("hook", ""), post.get("caption", ""), post.get("cta", "")]
    tags = " ".join(post.get("hashtags") or [])
    return "\n\n".join(p.strip() for p in [*parts, tags] if p and p.strip())
