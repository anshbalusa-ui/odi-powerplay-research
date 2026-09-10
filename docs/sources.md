# Source Notes

## Cricsheet

- Downloads: https://cricsheet.org/downloads/
- Official JSON format: https://cricsheet.org/format/json/
- Match data overview: https://cricsheet.org/matches/
- Register/licence information: https://cricsheet.org/register/
- Timestamp limitation: https://cricsheet.org/contact/

Use the official JSON format, record the snapshot date/checksum, and attribute Cricsheet in the paper. Cricsheet's site notes that some matches may be withheld, so the cohort description must report actual available counts rather than assuming complete coverage.

## Pitch-first scope decision

- Pitch hardness/moisture and performance: https://journals.sta.uwi.edu/ojs/index.php/ta/article/view/971/0
- Water content, compaction, bounce, pace, and turn: https://journals.sta.uwi.edu/ojs/index.php/wije/article/view/7735
- Cricket-ball swing and humidity: https://journals.sagepub.com/doi/abs/10.1177/1754337119872874
- ICC ODI playing-condition note on dew: https://www.icc-cricket.com/news/mens-odi-match-clause-12-start-of-play-cessation-of-play

The primary design does not collect generic hourly temperature, humidity, precipitation, cloud cover, wind speed, or dew point. Those variables do not directly describe the surface behavior at the center of the research question, while published cricket-ball research reports no significant effect of humidity in isolation on swing. The pitch code instead focuses on expected batting ease, pace/seam support, spin support, bounce, and two-paced behavior. An explicit pre-match dew expectation may be retained as a secondary condition because ODI playing conditions recognize dew as a match factor.

## ESPNcricinfo

- ESPN terms entry point: https://support.espn.com/hc/en-us/articles/360035445091-Terms-of-Use
- Governing Disney terms: https://disneytermsofuse.com/english/

Terms review on 2026-09-05 found that the governing terms prohibit using robots, scripts, or other automated means to copy or extract the products for data mining, web scraping, or building a dataset. Automated ESPNcricinfo collection is therefore disabled for this project unless written permission or a suitable licensed data route is obtained. Any proposed human coding workflow must also receive an appropriate rights/terms review before the resulting dataset is published. Do not reproduce report text; retain only permitted provenance metadata and short original research codes or paraphrases.

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
