# CONTEXT — competition rules digest + sources

Condensed from the full official rules. Full legal text: <https://www.kaggle.com/competitions/kaggriculture/rules>.
Nothing operational was dropped; the general boilerplate (eligibility, taxes, publicity, privacy,
indemnity, governing law) is summarized in §4.

## 1. Sources — top-scorer notebooks

Pulled locally to `research/notebooks/`, agents extracted to `bench/`. See `docs/META.md` for the analysis.

| Notebook | Note |
| --- | --- |
| [bovard — Kaggriculture Getting Started](https://www.kaggle.com/code/bovard/kaggriculture-getting-started) | Host baseline |
| [boatlee — V16-RC5 8C/4S Premium Market Lead](https://www.kaggle.com/code/boatlee/v16-rc5-high-score-8c-4s-premium-market-lead) | Replay-reconstructed route + 1-turn sell front-run |
| [kaitofukami — 15/16 Strict-Future v25 Meta Reset](https://www.kaggle.com/code/kaitofukami/15-16-strict-future-v25-meta-reset) | Meta audit; sell-slot reordering only |
| [andrewsokolovsky — Breaking the Tie](https://www.kaggle.com/code/andrewsokolovsky/kaggriculture-breaking-the-tie) | Mirror-detection + anti-front-run counter |

Referenced from those notebooks (not yet pulled):
Rayk Kretzschmar "Findings from Zero to Top Meta", cjlcjlcjl "What the Top Farms Do — a Live Meta",
revanthtambisetty "Two Private Bots Beating Kaggriculture Meta".

## 2. Competition-specific terms

- **Title / Sponsor:** Kaggriculture — Google LLC. Site: <https://www.kaggle.com/competitions/kaggriculture>
- **Prizes:** $50,000 total — ten prizes of $5,000 (1st through 10th).
- **Winner license:** CC-BY 4.0 (open-source your winning submission + source). Data use: Apache 2.0.
- **Team size:** max 5. Mergers allowed pre-deadline if combined submission count fits the cap.
- **Submission limit:** 5 per day; up to 2 final submissions selected for judging.
- **Timeline:** see the competition Overview → Timeline page (entry, merger, final deadlines).
- **Scoring:** episode-based leaderboard, aggregated. **No private leaderboard** in simulation comps.
- **Replays are public** and downloadable, including your agent's actions — so is everyone else's.
- **No ingress/egress:** during an episode the submission may not pull in or send out any external
  information. Everything must be self-contained.
- **Entry = acceptance of the rules.** One Kaggle account per person; multi-account = disqualification.

## 3. Code, data, and tooling rules

- **Private sharing is banned.** Sharing code outside your team is a DQ. Public sharing is allowed and
  is deemed licensed under an OSI-approved license — so reading and learning from public notebooks
  (as in §1) is explicitly fine.
- **Open source only** for any third-party code inside the submission; the license must not restrict
  commercial use.
- **External data / tools / LLMs allowed** if publicly available to all participants at reasonable cost
  ("Reasonableness Standard"). Small subscriptions OK; a dataset license costing more than the prize is not.
- **AutoML tools allowed**, provided you hold an appropriate license.
- **Winner obligations:** publish a reproducible write-up (methodology, architecture, hyper-parameters)
  plus a code repo, grant the CC-BY 4.0 license, sign prize/tax documents (W-9 / W-8BEN), possibly a
  recorded call.

## 4. General rules — summary

Standard Kaggle terms apply: 18+ and a registered account; residents of Crimea, DNR, LNR, Cuba, Iran,
North Korea and anyone under U.S. sanctions/export control are excluded; Kaggle hosts on Google's behalf
and does not pick winners; ties go to the earlier submission; disqualified or non-responsive winners are
replaced (one week to respond, two weeks to return documents, prizes paid ~30 days after); winners' taxes
are their own; sponsor may use your name for publicity; personal data is handled per Kaggle's privacy
policy; you warrant the submission is your original work and indemnify the sponsor; the sponsor may cancel,
modify, or disqualify for tampering; nothing here is an employment offer; California law governs.
