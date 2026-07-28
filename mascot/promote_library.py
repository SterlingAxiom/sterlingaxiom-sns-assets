#!/usr/bin/env python3
"""
Sterling Axiom マスコットライブラリ:合格品の確定とmanifest生成

前提:candidates/ を目視確認し、使えないものを削除済みであること。
     ここに残っているファイル = 田島さんが合格判定したもの、として扱う。

使い方:
    python3 promote_library.py
    python3 promote_library.py --transparent   # 背景を透過にする(要 rembg)

出力:
    approved/<pattern_id>__vN.png
    manifest.json   ← パイプラインはこれだけを見る
"""

import argparse
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATTERNS_PATH = HERE / "patterns.json"
CAND_DIR = HERE / "candidates"
APPROVED_DIR = HERE / "approved"
MANIFEST_PATH = HERE / "manifest.json"


def strip_background(src: Path, dest: Path) -> bool:
    """rembgで背景を透過にする。未インストールなら False を返して呼び出し側でフォールバック。"""
    try:
        from rembg import remove  # pip install rembg
    except ImportError:
        return False
    dest.write_bytes(remove(src.read_bytes()))
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transparent", action="store_true",
                    help="背景を透過PNGにする(rembgが必要)")
    args = ap.parse_args()

    if not CAND_DIR.exists():
        print("candidates/ がありません。先に generate_library.py を実行してください。",
              file=sys.stderr)
        return 1

    spec = json.loads(PATTERNS_PATH.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in spec["patterns"]}

    survivors = sorted(CAND_DIR.glob("*.png"))
    if not survivors:
        print("candidates/ が空です。全部削除してしまっていませんか?", file=sys.stderr)
        return 1

    APPROVED_DIR.mkdir(exist_ok=True)
    entries = []
    warned_rembg = False
    counts: dict[str, int] = defaultdict(int)

    for src in survivors:
        pattern_id = src.stem.split("__")[0]
        pattern = by_id.get(pattern_id)
        if pattern is None:
            print(f"  スキップ(未知のID): {src.name}", file=sys.stderr)
            continue

        dest = APPROVED_DIR / src.name
        done = False
        if args.transparent:
            done = strip_background(src, dest)
            if not done and not warned_rembg:
                print("  注意: rembg 未インストールのため透過処理をスキップします "
                      "(pip install rembg で有効化)", file=sys.stderr)
                warned_rembg = True
        if not done:
            shutil.copy2(src, dest)

        counts[pattern_id] += 1
        entries.append({
            "file": dest.name,
            "pattern_id": pattern_id,
            "label": pattern["label"],
            "emotion": pattern["emotion"],
            "framing": pattern["framing"],
            "use": pattern["use"],
        })

    manifest = {
        "version": 1,
        "note": "承認済みマスコット画像。パイプラインは select_mascot.py 経由でここから選ぶ。"
                "毎回のAI画像生成は行わない。",
        "assets": entries,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"承認済み: {len(entries)} 枚 -> {APPROVED_DIR}")
    print(f"manifest: {MANIFEST_PATH}")

    # 用途カバレッジの点検:欠けている切り口があれば警告する
    covered: dict[str, int] = defaultdict(int)
    for e in entries:
        for u in e["use"]:
            covered[u] += 1
    print("\n用途別の在庫:")
    for use in ["成長訴求型", "危機喚起型", "ランキング型", "ハウツー型", "説明", "汎用"]:
        n = covered.get(use, 0)
        flag = "  ← 少ない。補充を検討" if n < 3 else ""
        print(f"  {use}: {n}枚{flag}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
