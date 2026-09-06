import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .config import Profile, load_profile
from .digest import to_csv, to_markdown
from .models import Listing
from .scoring import rank
from .sources.base import Source
from .sources.freelancer_com import FreelancerComSource
from .sources.manual import ManualSource
from .sources.remoteok import RemoteOKSource
from .sources.remotive import RemotiveSource
from .sources.weworkremotely import WeWorkRemotelySource


def build_sources(profile: Profile, manual_file: Optional[str]) -> List[Source]:
    sources: List[Source] = []
    for name in profile.sources_enabled:
        if name == "manual":
            if manual_file:
                sources.append(ManualSource(manual_file))
            continue
        if name == "remotive":
            sources.append(RemotiveSource())
        elif name == "remoteok":
            sources.append(RemoteOKSource())
        elif name == "weworkremotely":
            sources.append(WeWorkRemotelySource(profile.wwr_feeds))
        elif name == "freelancer_com":
            sources.append(FreelancerComSource())
        else:
            print(f"[warn] unknown source '{name}' in config, skipping", file=sys.stderr)
    return sources


def gather(profile: Profile, manual_file: Optional[str]) -> List[Listing]:
    all_listings: List[Listing] = []
    for source in build_sources(profile, manual_file):
        try:
            found = source.fetch(profile.keywords)
        except Exception as exc:  # noqa: BLE001 - a broken source must not kill the run
            print(f"[warn] source {source.name} raised {exc!r}, skipping", file=sys.stderr)
            continue
        all_listings.extend(found)
    return all_listings


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Freelance work search agent")
    parser.add_argument("--config", default=None, help="Path to a config.yaml (default: bundled one)")
    parser.add_argument(
        "--manual-file",
        default=None,
        help="Path to pasted Upwork/Fiverr/etc. job posts (see manual_jobs.example.txt)",
    )
    parser.add_argument("--out", default=None, help="Write the markdown digest to this path")
    parser.add_argument("--csv", default=None, help="Also write ranked results to this CSV path")
    parser.add_argument("--top", type=int, default=None, help="Override top_n from config")
    parser.add_argument(
        "--email", action="store_true", help="Email the digest (see SETUP.md for required env vars)"
    )
    args = parser.parse_args(argv)

    profile = load_profile(args.config)
    if args.top:
        profile.top_n = args.top

    listings = gather(profile, args.manual_file)
    ranked = rank(listings, profile)[: profile.top_n]
    markdown = to_markdown(ranked, profile)

    if args.out:
        Path(args.out).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)

    if args.csv:
        to_csv(ranked, args.csv)

    if args.email:
        from .mailer import send_digest_email

        send_digest_email(markdown, subject=f"Freelance digest — {len(ranked)} matches")

    return 0


if __name__ == "__main__":
    sys.exit(main())
