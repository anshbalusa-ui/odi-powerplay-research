# Source Notes

## Cricsheet

- Downloads: https://cricsheet.org/downloads/
- Official JSON format: https://cricsheet.org/format/json/
- Match data overview: https://cricsheet.org/matches/
- Register/licence information: https://cricsheet.org/register/
- Cricsheet match-ID provenance: https://cricsheet.org/format/csv_ashwin/
- Timestamp limitation: https://cricsheet.org/contact/

Use the official JSON format, record the snapshot date/checksum, and attribute Cricsheet in the paper. Cricsheet's site notes that some matches may be withheld, so the cohort description must report actual available counts rather than assuming complete coverage.

## Pitch-first scope decision

- Pitch hardness/moisture and performance: https://journals.sta.uwi.edu/ojs/index.php/ta/article/view/971/0
- Water content, compaction, bounce, pace, and turn: https://journals.sta.uwi.edu/ojs/index.php/wije/article/view/7735
- Cricket-ball swing and humidity: https://journals.sagepub.com/doi/abs/10.1177/1754337119872874
- ICC ODI playing-condition note on dew: https://www.icc-cricket.com/news/mens-odi-match-clause-12-start-of-play-cessation-of-play

The primary design does not collect generic hourly temperature, humidity, precipitation, cloud cover, wind speed, or dew point. Those variables do not directly describe the surface behavior at the center of the research question, while published cricket-ball research reports no significant effect of humidity in isolation on swing. The pitch code instead focuses on expected batting ease, pace/seam support, spin support, bounce, and two-paced behavior. An explicit pre-match dew expectation may be retained as a secondary condition because ODI playing conditions recognize dew as a match factor.

## ESPNcricinfo

- Current ESPNcricinfo terms: https://www.espncricinfo.com/terms-of-use
- ESPN support terms entry point: https://support.espn.com/hc/en-us/articles/360035445091-Terms-of-Use
- Governing Disney terms: https://disneytermsofuse.com/english/

The current ESPNcricinfo terms were rechecked on 2026-09-10. They explicitly
prohibit using data-mining, robots, or similar collection or extraction tools.
Automated ESPNcricinfo collection is therefore disabled unless written permission
or a suitable licensed route is obtained. Any proposed human coding workflow must
also receive a rights review before publication. Do not reproduce report text;
retain only permitted provenance metadata and short original research codes or
paraphrases.

### Rights-safe ESPN identifier handoff

Cricsheet's official Ashwin-format documentation says its file `<id>` is the
Cricinfo match ID and separately warns that the Cricsheet `match_id` is generally,
but not guaranteed to be, the Cricinfo ID. The pipeline therefore treats each
numeric primary-cohort ID as an **unverified candidate**, never as a confirmed ESPN
mapping.

For all 1,094 primary matches, the outcome-blind queue now includes the numeric
candidate, an unfetched legacy ESPN match-URL candidate, blank verified-ID and
verified-URL fields, and an explicit linkage status. Candidate generation performs
zero network requests and imports no ESPN text, score, commentary, or page metadata.
The legacy URL is navigation assistance only; it can be stale, redirect, or identify
the wrong match.

A human or licensed collector must compare teams, date, event, and venue before
setting `espn_linkage_status=verified_match`, then record the actual numeric ESPN ID
and current ESPN match URL. `audit_espn_linkage.py` rejects malformed candidates,
unsupported statuses, duplicate Cricsheet IDs, and a claimed verified mapping
without a valid ESPNcricinfo URL. `validate_pitch_rows` additionally refuses a
verified ESPN source row unless this independent match-linkage gate has passed.


### Third-party commentary dataset review

Potential substitutes were checked rather than accepted from their uploader labels:

- Kaggle's *Cricket Scorecard and Commentary Dataset* covers roughly 2017–2020
  international and league matches, but its API metadata reports the licence as
  `Unknown`. It cannot support a redistributable research pipeline.
  Metadata: https://www.kaggle.com/api/v1/datasets/view/raghuvansht/cricket-scorecard-and-commentary-dataset
- Kaggle's *Ultimate Ball-by-Ball Cricket Dataset* is labelled CC0 by its uploader,
  but its own description says the commentary and enriched fields were scraped from
  ESPNcricinfo. An uploader declaration does not establish rights to relicense the
  underlying ESPN material. Its line, length, shot, and direction fields also do
  not constitute match-level pre-match pitch conditions.
  Metadata: https://www.kaggle.com/api/v1/datasets/view/ariadaikalam/the-ultimate-ball-by-ball-cricket-dataset
- Kaggle's CC0-labelled *Cricket Commentary Dataset* points to a small Hugging Face
  text-generation dataset but documents no match-ID/date/venue join keys or
  authoritative source provenance. It cannot be aligned to the primary ODI cohort
  or establish pre-match timing.
  Metadata: https://www.kaggle.com/api/v1/datasets/view/thedevastator/cricket-commentary-dataset

None of these datasets is imported. A claimed dataset licence is not treated as
permission to republish source text when provenance or underlying rights are
unresolved, and post-start commentary remains temporally ineligible regardless of
licence.

## Pitch-source search protocol

Pitch reports are collected in outcome-blind batches. Match IDs are selected before any report, scorecard, powerplay value, or result is inspected. For each selected match, search in this order:

1. match-specific pre-match ESPNcricinfo or ICC report;
2. the relevant national cricket board or an established local/international news outlet;
3. an established specialist cricket outlet when the first two levels have no surface description.

Fantasy-prediction, betting, unattributed aggregator, social-media, live-blog, and post-match pages do not establish the primary pitch code. When higher-quality sources lack pitch evidence or lower-quality sources conflict, leave pitch dimensions missing and record the reason. One missing-source row is preferable to an unsupported classification.

ESPNcricinfo ball-by-ball commentary and match-day live coverage are never pitch
inputs: they are post-start sources, can reveal powerplay performance and outcome
information, and are outside the permitted automated-use policy. Only a separately
identified match preview or pre-match conditions report can qualify.

The working file distinguishes `source_no_pitch_evidence` from `no_eligible_source`. This makes it possible to separate a coverage problem from a source that exists but says nothing usable about the playing surface.
