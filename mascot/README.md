# Sterling Axiom マスコット事前生成ライブラリ

投稿ごとにAI画像生成を回すのをやめ、**事前に生成 → 田島さんが目視で選別 → 承認済みだけを使い回す**
方式に切り替えるための一式です。

## 置き場所

`sterlingaxiom-sns-assets` リポジトリの `mascot/` 配下に置くことを想定しています。

```
sterlingaxiom-sns-assets/
└── mascot/
    ├── base.png                    # 既存(確定済みの基本デザイン)
    ├── patterns.json               # 生成パターン定義(30種)
    ├── generate_library.py         # ①候補を一括生成
    ├── promote_library.py          # ②残ったものを承認済みに確定
    ├── select_mascot.py            # ③パイプラインから呼ぶ選択モジュール
    ├── candidates/                 # 生成直後の候補(選別作業用・Git管理不要)
    ├── approved/                   # 承認済み(Public公開。ここのURLを使う)
    └── manifest.json               # 承認済み画像のインデックス
```

`candidates/` と `usage_log.json` は `.gitignore` に入れてください。

## 初回セットアップ(所要:生成の待ち時間を除けば30分程度)

### 準備

`select_mascot.py` の `RAW_URL_TEMPLATE` の `<owner>` を、実際のGitHubアカウント名に
置き換えてください。ここだけは手作業が必要です。

### ① 候補を一括生成

```bash
cd mascot
python3 generate_library.py \
  --base-url "https://raw.githubusercontent.com/<owner>/sterlingaxiom-sns-assets/main/mascot/base.png"
```

- 30パターン × 4枚 = 120枚。待機2秒込みで**おおむね30〜60分**かかります。放置して構いません
- APIキーは不要です(Pollinations.aiは無料・認証不要)
- `kontext`(base.png参照)を優先し、失敗した場合のみ `flux` に自動フォールバックします
- 途中で失敗した分は後から `--only` で作り直せます

```bash
python3 generate_library.py --only alert_guard,rank_trophy --variants 6
```

### ② Finderで目視選別 ← ここが品質の要

`candidates/` フォルダをFinderで開き、**ギャラリー表示**(表示メニュー → ギャラリー)にします。
矢印キーで送りながら、以下に当てはまるものを `⌘+Delete` で削除してください。

- 手・指の破綻(本数がおかしい、歪んでいる)
- 腕や脚が本来ない場所から生えている
- 顔や輪郭の崩れ、「AI生成感」の強い不自然さ
- **4本足で立っている**(擬人化コンセプトとの矛盾)
- 犬種・配色・服装が base.png から大きく逸脱している

判断に迷ったら削除してください。**残す枚数より、残すものの質が重要です。**
1パターンにつき1枚残れば十分です。全滅したパターンは後で `--only` で作り直します。

なお `patterns.json` の `framing: "bust"` は腰から上だけを描かせる指定で、
「4本足になる」「脚が変な場所から生える」破綻が原理的に起きません。30種のうち約2/3を
bustにしてあるため、歩留まりは高いはずです。

### ③ 承認済みに確定

```bash
python3 promote_library.py
# 背景を透過にする場合(推奨・要 pip install rembg)
python3 promote_library.py --transparent
```

`approved/` に承認済み画像がコピーされ、`manifest.json` が生成されます。
最後に用途別の在庫が表示されるので、3枚未満の切り口があれば ① に戻って補充してください。

### ④ GitHubにpush

```bash
git add mascot/approved mascot/manifest.json mascot/*.py mascot/patterns.json
git commit -m "マスコット承認済みライブラリを追加"
git push
```

### ⑤ 動作確認

```bash
python3 select_mascot.py --use 危機喚起型
```

返ってきた `raw_url` をブラウザで開いて、画像が表示されれば完了です。

### ⑥ スキルを更新

`SKILL_step4_差し替え案.md` の内容を確認し、問題なければ
`sterling-axiom-sns/SKILL.md` のステップ4に反映してください。

## 運用中の補充(月1回程度)

単調さを避けるため、月1回を目安に5〜10パターン追加します。

1. `patterns.json` の `patterns` 配列に新しい項目を追加する
2. `python3 generate_library.py --only <新しいID> --base-url ...`
3. Finderで選別
4. `python3 promote_library.py`
5. push

## 既知の制約

- **Pollinations.aiの応答は不安定なことがあります。** 失敗したパターンは `--only` で再実行してください
- **クラウド実行環境(Routine)では生成できません。** ネットワーク許可ドメインに
  `image.pollinations.ai` が含まれていないためです。生成は必ずローカルのMacで行ってください。
  日次パイプライン側は `manifest.json` と GitHub の raw URL しか見ないため、クラウドでも動きます
- `--transparent` には `rembg` が必要です。未インストールの場合は透過処理をスキップして
  白背景のままコピーします(処理は止まりません)
