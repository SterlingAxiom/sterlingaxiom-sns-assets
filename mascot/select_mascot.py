#!/usr/bin/env python3
"""
Sterling Axiom マスコットライブラリ:投稿タイプに応じた画像の選択

日次パイプラインのステップ4から呼ばれる。AI画像生成は一切行わない。

CLI:
    python3 select_mascot.py --use 危機喚起型
    python3 select_mascot.py --use ランキング型 --framing full

Python:
    from select_mascot import select
    asset = select(use="成長訴求型")
    print(asset["raw_url"])

直近で使ったものを usage_log.json に記録し、同じ絵が連続しないようにする。
"""

import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST_PATH = HERE / "manifest.json"
USAGE_LOG = HERE / "usage_log.json"

# GitHubの公開rawURLのテンプレート。<owner> は実際のアカウント名に置き換える。
RAW_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/SterlingAxiom/sterlingaxiom-sns-assets"
    "/main/mascot/approved/{file}"
)

# 直近この件数に使ったファイルは避ける
RECENT_WINDOW = 8


def _load_recent() -> list[str]:
    if USAGE_LOG.exists():
        try:
            return json.loads(USAGE_LOG.read_text(encoding="utf-8")).get("recent", [])
        except json.JSONDecodeError:
            return []
    return []


def _record(filename: str) -> None:
    recent = [f for f in _load_recent() if f != filename]
    recent.insert(0, filename)
    USAGE_LOG.write_text(
        json.dumps({"recent": recent[:RECENT_WINDOW]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")


def select(use: str, framing: str | None = None, record: bool = True) -> dict:
    """use(投稿の切り口)に合う承認済み画像を1枚返す。"""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            "manifest.json がありません。promote_library.py を先に実行してください。")

    assets = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["assets"]

    pool = [a for a in assets if use in a["use"]]
    if framing:
        pool = [a for a in pool if a["framing"] == framing]
    if not pool:
        # 該当なしのときは汎用にフォールバック(処理は止めない)
        pool = [a for a in assets if "汎用" in a["use"]] or assets
    if not pool:
        raise ValueError("承認済み画像が1枚もありません。")

    recent = _load_recent()
    fresh = [a for a in pool if a["file"] not in recent]
    chosen = random.choice(fresh or pool)

    if record:
        _record(chosen["file"])

    return {**chosen, "raw_url": RAW_URL_TEMPLATE.format(file=chosen["file"])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--use", required=True,
                    help="成長訴求型 / 危機喚起型 / ランキング型 / ハウツー型 / 説明 / 汎用")
    ap.add_argument("--framing", choices=["bust", "full"], default=None)
    ap.add_argument("--no-record", action="store_true",
                    help="使用履歴に記録しない(お試し用)")
    args = ap.parse_args()

    try:
        asset = select(args.use, args.framing, record=not args.no_record)
    except (FileNotFoundError, ValueError) as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1

    print(json.dumps(asset, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
