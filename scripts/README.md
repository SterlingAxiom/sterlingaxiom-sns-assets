# 人気投稿の構造分析スクリプト(補助ツール)

`sterling-axiom-sns` スキルのステップ1.5(人気投稿の構造分析)で使う補助スクリプト。
**日次の自動投稿パイプラインには組み込まれていない。人がローカル環境(自分のMac)で明示的に実行する任意ツール。**

## 前提とリスク

- `x_popular_posts.py`(X/Twitter)と `instagram_popular_posts.py`(Instagram)は、いずれも**非公式スクレイピングツール**を使う
  - X: [twscrape](https://github.com/vladkens/twscrape)
  - Instagram: [Instaloader](https://github.com/instaloader/instaloader)
- 非公式ツールのため、両プラットフォームの利用規約(ToS)違反にあたる。アカウント凍結・機能制限のリスクを理解した上で、自己責任で使うこと
- **投稿用のメインアカウント(ブランドアカウント)の認証情報は絶対に使わない。** X用には専用の読み取り専用アカウントを別途用意すること。Instagram側は未認証(ログインなし)で公開ハッシュタグの投稿のみを取得するため、アカウント登録は不要
- LinkedInの補助スクリプトは用意していない。LinkedInは判例(hiQ Labs対LinkedIn等)で非公式スクレイピングが契約違反と認定されており、他媒体よりリスクが高い。加えてSterling AxiomのLinkedIn運用は代表個人アカウントのため、Web検索による間接調査のみに留める(スキル本体のステップ1.5を参照)
- ツールの性質上、プラットフォーム側の仕様変更で頻繁に壊れる(実際に `snscrape` は2024〜2025年にかけて機能停止した)。動かなくなった場合は無理に直そうとせず、Web検索による代替調査にフォールバックする

## セットアップ

```bash
pip install twscrape instaloader
```

### X(twscrape)

1. 投稿用メインアカウントとは別の、読み取り専用の予備アカウントを用意する
2. アカウントを`twscrape`に登録する(一度だけ)

```bash
twscrape add_account <username> <password> <email> <email_password>
twscrape login_accounts
```

3. 環境変数で読み取り専用アカウントのユーザー名を明示しておく(誤ってメインアカウントを使わないための確認用)

```bash
export TWSCRAPE_READONLY_USERNAME="<予備アカウントのusername>"
```

### Instagram(instaloader)

追加のセットアップ不要(未認証・公開ハッシュタグのみを取得するため)。

## 使い方

```bash
# X: キーワードで検索し、エンゲージメント上位の投稿を構造分析
python scripts/x_popular_posts.py --keywords "生成AI 業務改善" "AI 導入 中小企業" --limit 30 --top 10

# Instagram: ハッシュタグの人気投稿を構造分析
python scripts/instagram_popular_posts.py --hashtags AIツール ChatGPT活用 --top 10
```

いずれも標準出力にJSONで結果を出す。各投稿について以下を出力する(本文全文はコピー・転載目的では保持しない。構造分析にのみ使う):

- `engagement`(いいね・リポスト・返信等の合計)
- `text_length`(文字数)
- `hashtag_count`
- `line_break_count`(改行の数、フックの型を見るため)
- `opening_line`(冒頭1文、フックのパターン分析用)
- `has_media`

## 出力の使い方

このJSONを丸ごとNotionに保存せず、`sterling-axiom-sns` スキルのステップ1.5に従い、**パターンの要約(例:「数字を含む問いかけで始まる投稿が上位に多い」)にまとめてから**、ステップ3(投稿文作成)・ステップ4(画像生成)の参考にすること。
