#!/usr/bin/env python3
"""X(Twitter)の人気投稿を検索し、構造(型)を分析する補助スクリプト。

非公式ライブラリ twscrape (https://github.com/vladkens/twscrape) を使う。
投稿用メインアカウントとは別の、専用の読み取り専用アカウントで
`twscrape add_account` / `twscrape login_accounts` を事前に済ませておくこと。

本文全文は保持・出力しない(構造分析のみが目的)。

使い方:
    python x_popular_posts.py --keywords "生成AI 業務改善" "AI 導入 中小企業" --limit 30 --top 10
"""
import argparse
import asyncio
import json
import re

from twscrape import API


def analyze_tweet(tweet) -> dict:
    text = tweet.rawContent or ""
    lines = text.splitlines()
    engagement = (
        (tweet.likeCount or 0)
        + (tweet.retweetCount or 0)
        + (tweet.replyCount or 0)
        + (tweet.quoteCount or 0)
    )
    return {
        "engagement": engagement,
        "likeCount": tweet.likeCount,
        "retweetCount": tweet.retweetCount,
        "replyCount": tweet.replyCount,
        "text_length": len(text),
        "hashtag_count": len(re.findall(r"#\w+", text)),
        "line_break_count": text.count("\n"),
        "opening_line": lines[0] if lines else "",
        "has_media": bool(tweet.media and (tweet.media.photos or tweet.media.videos)),
        "date": tweet.date.isoformat() if tweet.date else None,
        "url": tweet.url,
    }


async def run(keywords: list[str], limit: int, top: int) -> list[dict]:
    api = API()
    results: list[dict] = []
    for kw in keywords:
        async for tweet in api.search(kw, limit=limit):
            results.append(analyze_tweet(tweet))
    results.sort(key=lambda r: r["engagement"], reverse=True)
    return results[:top]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keywords", nargs="+", required=True, help="検索キーワード(複数可)")
    parser.add_argument("--limit", type=int, default=30, help="キーワードごとの取得件数上限")
    parser.add_argument("--top", type=int, default=10, help="エンゲージメント上位から出力する件数")
    args = parser.parse_args()

    results = asyncio.run(run(args.keywords, args.limit, args.top))
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
