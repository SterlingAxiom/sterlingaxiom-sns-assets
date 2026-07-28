#!/usr/bin/env python3
"""
Sterling Axiom マスコットライブラリ:候補画像の一括生成

使い方(Claude Code / ローカルMacで実行):
    python3 generate_library.py --base-url "https://raw.githubusercontent.com/<owner>/sterlingaxiom-sns-assets/main/mascot/base.png"

    # 一部のパターンだけ作り直す
    python3 generate_library.py --only alert_guard,rank_trophy --variants 6

出力:
    candidates/<pattern_id>__v1.png, v2.png, ...

生成後、Finderで candidates/ をギャラリー表示にして目視確認し、
使えないものをその場で削除する。残ったものが合格品。
そのあと promote_library.py を実行する。

APIキー不要(Pollinations.aiは無料・認証不要)。
"""

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATTERNS_PATH = HERE / "patterns.json"
OUT_DIR = HERE / "candidates"

ENDPOINT = "https://image.pollinations.ai/prompt/"
TIMEOUT = 180


def build_prompt(base: dict, pattern: dict) -> str:
    """共通の外見指定 + 個別ポーズ。Fluxは参照画像を使えないため毎回フル記述する。"""
    return f"{base['positive']}, {pattern['prompt']}"


def fetch(prompt: str, negative: str, size: dict, seed: int,
          model: str, ref_url: str | None) -> bytes | None:
    params = {
        "width": size["width"],
        "height": size["height"],
        "seed": seed,
        "model": model,
        "nologo": "true",
        "negative": negative,
    }
    if model == "kontext" and ref_url:
        params["image"] = ref_url

    url = ENDPOINT + urllib.parse.quote(prompt, safe="") + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "sterling-axiom-mascot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = r.read()
        # 極端に小さい応答はエラーページの可能性が高い
        if len(data) < 5000:
            return None
        return data
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"      ! {model} 失敗: {e}", file=sys.stderr)
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=None,
                    help="base.png の公開raw URL(kontextモデルの参照画像に使う)")
    ap.add_argument("--variants", type=int, default=4,
                    help="1パターンあたりの生成枚数(既定4)")
    ap.add_argument("--only", default=None,
                    help="対象パターンIDをカンマ区切りで指定")
    ap.add_argument("--sleep", type=float, default=2.0,
                    help="リクエスト間の待機秒数")
    args = ap.parse_args()

    spec = json.loads(PATTERNS_PATH.read_text(encoding="utf-8"))
    base, patterns = spec["base"], spec["patterns"]

    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        patterns = [p for p in patterns if p["id"] in wanted]
        missing = wanted - {p["id"] for p in patterns}
        if missing:
            print(f"警告: 未知のパターンID: {', '.join(sorted(missing))}", file=sys.stderr)

    if not patterns:
        print("対象パターンがありません。", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(exist_ok=True)
    total = ok = 0

    for i, pattern in enumerate(patterns, 1):
        prompt = build_prompt(base, pattern)
        print(f"[{i}/{len(patterns)}] {pattern['id']} — {pattern['label']}")

        for v in range(1, args.variants + 1):
            total += 1
            seed = random.randint(1, 10**9)
            data = None

            # ①kontext(参照画像あり)を優先、②失敗したらflux
            if args.base_url:
                data = fetch(prompt, base["negative"], base["size"], seed,
                             "kontext", args.base_url)
            if data is None:
                data = fetch(prompt, base["negative"], base["size"], seed,
                             "flux", None)

            if data is None:
                print(f"    v{v}: 失敗(スキップ)")
            else:
                dest = OUT_DIR / f"{pattern['id']}__v{v}.png"
                dest.write_bytes(data)
                ok += 1
                print(f"    v{v}: OK -> {dest.name}")

            time.sleep(args.sleep)

    print(f"\n完了: {ok}/{total} 枚を {OUT_DIR} に保存しました。")
    print("次の手順: Finderで candidates/ をギャラリー表示にして目視確認 →")
    print("          使えないものを削除 → python3 promote_library.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
