#!/usr/bin/env python3
"""Instagramのハッシュタグ人気投稿を取得し、構造(型)を分析する補助スクリプト。

非公式ライブラリ Instaloader (https://github.com/instaloader/instaloader) を使う。
**未認証(ログインなし)で公開ハッシュタグの投稿のみを取得する**運用にすること
(ログインするとアカウント凍結リスクが上がるため)。

本文全文は保持・出力しない(構造分析のみが目的)。

使い方:
    python instagram_popular_posts.py --hashtags AIツール ChatGPT活用 --top 10
"""
import argparse
import json

import instaloader


def analyze_post(post) -> dict:
    caption = post.caption or ""
    lines = caption.splitlines()
    return {
        "likes": post.likes,
        "comments": post.comments,
        "caption_length": len(caption),
        "hashtag_count": len(post.caption_hashtags),
        "line_break_count": caption.count("\n"),
        "opening_line": lines[0] if lines else "",
        "is_video": post.is_video,
        "date": post.date_utc.isoformat() if post.date_utc else None,
        "url": f"https://www.instagram.com/p/{post.shortcode}/",
    }


def run(hashtags: list[str], top: int) -> dict[str, list[dict]]:
    loader = instaloader.Instaloader()
    output: dict[str, list[dict]] = {}
    for tag in hashtags:
        posts = []
        try:
            hashtag = instaloader.Hashtag.from_name(loader.context, tag)
            for post in hashtag.get_top_posts():
                posts.append(analyze_post(post))
        except Exception as exc:  # noqa: BLE001 - 取得失敗はスキップして続行
            output[tag] = [{"error": str(exc)}]
            continue
        posts.sort(key=lambda p: p.get("likes", 0), reverse=True)
        output[tag] = posts[:top]
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hashtags", nargs="+", required=True, help="調査するハッシュタグ(#は不要、複数可)")
    parser.add_argument("--top", type=int, default=10, help="ハッシュタグごとに出力する上位件数")
    args = parser.parse_args()

    result = run(args.hashtags, args.top)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
