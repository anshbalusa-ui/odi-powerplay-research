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
and current match URL. `audit_espn_linkage.py` rejects malformed candidates,
unsupported statuses, duplicate Cricsheet IDs, and a claimed verified mapping
without an ESPNcricinfo URL or a canonical ESPN cricket URL. Outcome-free ESPN
print views with a numeric article ID are accepted as preview-source URLs, but they
still require the independent match-linkage gate.


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

## Scheduled-start sources

Scheduled starts are collected separately from pitch descriptions so a timestamp
cannot smuggle score, commentary, or result fields into pitch coding. Prefer an
official tournament, ICC, or national-board schedule; a rights-permitted match page
may be used when it identifies the same teams, local date, event, and venue. ESPN
candidate IDs remain unfetched unless a human or licensed route performs that
verification. The repository stores only source provenance and the scheduled local
and UTC timestamps, not page text.

The verifier records an IANA timezone name so historical daylight-saving rules are
applied rather than guessing a fixed offset. `audit_match_start_times.py` checks the
local-to-UTC conversion and full cohort identity without making network requests.
A post-match page may corroborate the historical scheduled-start fact, but no score,
commentary, toss, lineup, or result may be transferred from it, and start-time
verification must remain separate from outcome-blind pitch coding.

## Pitch-source search protocol

Pitch reports are collected in outcome-blind batches. Match IDs are selected before any report, scorecard, powerplay value, or result is inspected. For each selected match, search in this order:

1. ICC or the relevant national cricket board;
2. an established local or international news outlet;
3. an established specialist cricket outlet when the first two levels have no surface description.

Fantasy-prediction, betting, unattributed aggregator, social-media, live-blog, and post-match pages do not establish the primary pitch code. When higher-quality sources lack pitch evidence or lower-quality sources conflict, leave pitch dimensions missing and record the reason. One missing-source row is preferable to an unsupported classification.

`validate_pitch_rows` enforces the obvious URL/title markers for fantasy,
Dream11, betting, and match-prediction pages. Ambiguous source quality,
attribution, and match linkage still require manual review.

ESPNcricinfo ball-by-ball commentary and match-day live coverage are never pitch
inputs: they are post-start sources, can reveal powerplay performance and outcome
information, and are outside the permitted automated-use policy. Only a separately
identified match preview or pre-match conditions report can qualify.

The working file distinguishes `source_no_pitch_evidence` from `no_eligible_source`. This makes it possible to separate a coverage problem from a source that exists but says nothing usable about the playing surface.

## First-batch source release

The first 25 outcome-blind matches were reviewed individually on 2026-09-11.
Four non-ESPN reports met the match-specific, pre-start, surface-evidence, and
provenance requirements:

- SportsJOE, South Africa–Ireland World Cup preview:
  https://www.sportsjoe.ie/world-of-sport/ireland-south-africa-cricket-world-cup-preview-15358
- Cricket Times, South Africa–England Champions Trophy pitch report:
  https://crickettimes.com/2025/03/sa-vs-eng-champions-trophy-2025-national-stadium-pitch-report-karachi-weather-forecast-odi-stats-and-records-south-africa-vs-england/
- Hindustan Times, New Zealand–India Auckland pitch report:
  https://www.hindustantimes.com/cricket/india-vs-new-zealand-2nd-odi-auckland-weather-and-pitch-report-chances-of-rain-in-the-afternoon-at-eden-park-ind-vs-nz-2nd-odi/story-q4YCarQ32Yiym03hfdVmAK.html
- ICC, Zimbabwe–Ireland World Cup Qualifier preview:
  https://www.icc-cricket.com/tournaments/cricketworldcup/news/ireland-look-to-inflict-first-defeat-on-zimbabwe

Four ESPN preview candidates were found for Cricsheet match IDs `1388412`,
`1130738`, `1075506`, and `1243395`. They are not in the verified release because
the current collection was AI-assisted rather than human/licensed. They remain in
`data/manual/pitch_set_aside.csv` for permitted follow-up. The repository publishes
no ESPN article passage.

## Second-batch source release

The second 25-match outcome-blind batch was reviewed individually on 2026-09-11.
Five non-ESPN reports met the same requirements:

- MyKhel, England–Netherlands Pune pitch/weather report:
  https://www.mykhel.com/cricket/mca-stadium-pune-pitch-report-weather-forecast-for-eng-vs-ned-icc-odi-world-cup-2023-match-40-244161.html
- MyKhel, Pakistan–South Africa Karachi pitch/weather report:
  https://www.mykhel.com/cricket/pakistan-vs-south-africa-3rd-odi-pak-vs-sa-pitch-weather-forecast-karachi-national-stadium-report-340299.html
- MyKhel, New Zealand–Pakistan Karachi final preview and pitch report:
  https://www.mykhel.com/cricket/nz-vs-pak-playing-11-odi-tri-series-final-new-zealand-vs-pakistan-probable-playing-xi-preview-weather-and-pitch-report-340972.html
- CricTracker, Ireland–South Africa second ODI match preview:
  https://www.crictracker.com/cricket-previews/ireland-vs-south-africa-match-preview-2nd-odi-2409-4246/
- Cricket Addictor, West Indies–Bangladesh Guyana match preview:
  https://cricketaddictor.com/cricket/windies-vs-bangladesh-2018-1st-odi-guyana-match-preview/

Twenty second-batch matches were set aside. Seven indexed surface descriptions
were deliberately rejected because they were fantasy/match-prediction pages, as
prohibited by the source protocol; one additional preview contained inconsistent
venue attribution. The remaining set-aside reasons identify inaccessible,
ESPN-only, or absent match-specific evidence.

The tracked `pitch_reports_verified.csv` contains only source URLs, publication and
access timestamps, derived categorical codes, and short original paraphrases.
These AI-assisted primary codes remain provisional until the independent human
reliability gate is satisfied.

## Third-batch source release

The third 25-match outcome-blind batch was reviewed individually on 2026-09-11.
Nine non-ESPN reports met the match-specific, pre-start, surface-evidence, and
provenance requirements:

- MyKhel, India–New Zealand Champions Trophy final toss and pitch report:
  https://www.mykhel.com/cricket/india-vs-new-zealand-toss-playing-11-update-for-champions-trophy-2025-final-rohit-sharma-loses-tos-346037.html
- ICC, England–Pakistan Champions Trophy semi-final preview:
  https://www.icc-cricket.com/news/advantage-england-but-that-counts-for-little
- CricTracker, Ireland–South Africa first ODI match preview:
  https://www.crictracker.com/cricket-previews/ireland-vs-south-africa-match-preview-1st-odi/
- Business Standard, India–New Zealand Rajkot pitch report:
  https://www.business-standard.com/cricket/news/india-vs-new-zealand-2nd-odi-rajkot-pitch-report-key-stadium-stats-126011300726_1.html
- ICC, New Zealand–South Africa Hamilton preview:
  https://www.icc-cricket.com/news/new-zealand-v-south-africa-4th-odi-hamilton-preview
- Cricket Australia, Australia–South Africa St Kitts preview:
  https://www.cricket.com.au/news/3272889/history-points-to-runs-fest-in-st-kitts
- ICC, New Zealand–Sri Lanka World Cup preview:
  https://www.icc-cricket.com/tournaments/cricketworldcup/news/confident-new-zealand-ready-to-kick-off-their-world-cup-campaign
- Cricket Australia, New Zealand–Australia Eden Park preview:
  https://www.cricket.com.au/news/3287986
- Daily Times, Pakistan–Australia Sharjah preview:
  https://dailytimes.com.pk/368951/pakistan-take-on-australia-in-second-odi-today/

Sixteen third-batch matches were set aside. One located pitch article was
published after the scheduled start, one indexed non-ESPN preview could not be
opened for direct review, and the remaining searches produced only ESPN-restricted,
generic, post-match, fantasy/betting, or surface-free pre-match material.

## Fourth-batch source release

The fourth 25-match outcome-blind batch was reviewed individually on 2026-09-11.
Ten non-ESPN reports met the source, timing, and surface-evidence requirements:

- Cricket Ireland, Ireland–West Indies second ODI preview:
  https://cricketireland.ie/news/match-preview-ireland-v-west-indies-2nd-odi/
- Cricket Australia, Australia–New Zealand SCG preview:
  https://www.cricket.com.au/news/3279017/pace-on-the-menu-as-rivalry-resumes
- Cricket Addictor, Sri Lanka–England second ODI preview:
  https://cricketaddictor.com/cricket-news/sl-vs-eng-2nd-odi-preview-free-live-streaming-pitch-weather-report-head-to-head-stats-records-england-tour-of-sri-lanka-2026-380450/
- MyKhel, Bangladesh–Sri Lanka Pallekele pitch/weather report:
  https://www.mykhel.com/cricket/bangladesh-vs-sri-lanka-asia-cup-2023-kandy-stadium-pitch-report-weather-forecast-230193.html
- ICC, Sri Lanka–South Africa Champions Trophy preview:
  https://www.icc-cricket.com/news/preview-sri-lanka-v-south-africa
- Telegraph India, Pakistan–Bangladesh Eden Gardens pitch report:
  https://www.telegraphindia.com/sports/cricket/pakistan-vs-bangladesh-eden-gardens-pitch-likely-to-aid-quicks-with-extra-bounce/cid/1976525
- The Daily Star, Sri Lanka–Bangladesh toss-time pitch assessment:
  https://www.thedailystar.net/star-multimedia/sports-multimedia/asia-cup-2023/news/nasum-tigers-opt-bowl-against-sl-3414611
- Business Standard, England–India Lord's pitch/weather report:
  https://www.business-standard.com/article/sports/eng-vs-ind-2nd-odi-pitch-report-and-weather-update-of-lord-s-london-122071301195_1.html
- Hindustan Times, India–New Zealand Dharamsala pitch report:
  https://www.hindustantimes.com/cricket/india-vs-nz-cool-dharamsala-could-offer-slight-advantage-to-medium-pacers/story-Jv52G9MTn6UMOuN7qVy6AI.html
- MyKhel, Pakistan–New Zealand Champions Trophy pitch/weather report:
  https://www.mykhel.com/cricket/champions-trophy-2025-pakistan-vs-new-zealand-pak-vs-nz-pitch-and-weather-forecast-karachi-stadium-341833.html

Fifteen fourth-batch matches were set aside. Reasons include publication after
start, date-only publication metadata that could not pass the precise timing gate,
inaccessible pages, surface-free official previews, fantasy/live/post-match
material, and absent match-specific evidence. Every reviewed working row records
the batch collection instant in `accessed_at_utc`; accepted rows separately retain
the source publication instant and verified scheduled-start instant.

## Fifth-batch source release

The fifth 25-match outcome-blind batch was selected newest-first from the unreviewed
queue and reviewed individually on 2026-09-11. Five non-ESPN reports met the source,
timing, and surface-evidence requirements:

- MyKhel, England–India Lord's pitch and team-news preview:
  https://www.mykhel.com/cricket/india-vs-england-3rd-odi-lords-weather-forecast-pitch-report-probable-xis-and-match-preview-447347.html
- Business Standard, England–India Cardiff preview and pitch report:
  https://www.business-standard.com/amp/cricket/news/england-vs-india-2nd-odi-playing-11-live-time-ist-cardiff-stadium-stats-126071600275_1.html
- Business Standard, England–India Edgbaston toss-time surface assessment:
  https://www.business-standard.com/cricket/news/eng-vs-ind-1st-odi-where-to-watch-live-streaming-of-today-s-cricket-match-126071300656_1.html
- The Daily Star, Zimbabwe–Bangladesh Harare preview:
  https://www.thedailystar.net/sports/cricket/news/tigers-bank-pacers-after-test-setback-4216626
- The Daily Star, Bangladesh–Australia Mirpur preview:
  https://www.thedailystar.net/sports/cricket/news/labuschagne-looking-salvage-pride-dead-rubber-4197761

Twenty fifth-batch matches were set aside. Official series previews without surface
analysis, generic venue history, post-start/live material, and fantasy-prediction
pages did not pass the match-specific pre-start evidence gate. All 25 working rows
record the common collection instant `2026-09-11T23:39:43Z`; accepted rows separately
retain the exact source-publication and scheduled-start instants. The reviewed match
range is 2026-06-06 through 2026-08-13.

## Sixth-batch source release

The sixth 25-match outcome-blind batch was selected newest-first and reviewed
individually on 2026-09-11. Eight non-ESPN reports met the source, timing, and
surface-evidence requirements:

- Dawn, Pakistan–Australia Lahore second-ODI preview:
  https://www.dawn.com/news/2004513
- Dawn, Pakistan–Australia Lahore third-ODI preview:
  https://www.dawn.com/news/2004997
- The Daily Star, Bangladesh–New Zealand Chattogram pitch assessment:
  https://www.thedailystar.net/sports/cricket/news/beauty-pitch-puzzle-awaits-series-decider-4158331
- Cricket Times, Sri Lanka–England Colombo first-ODI pitch report:
  https://crickettimes.com/2026/01/sl-vs-eng-pitch-report-for-1st-odi-r-premadasa-stadium-stats-and-records/
- Business Standard, India–New Zealand Indore pitch report:
  https://www.business-standard.com/amp/cricket/news/india-vs-new-zealand-3rd-odi-indore-pitch-report-key-stadium-stats-126011700947_1.html
- Business Standard, India–New Zealand Vadodara pitch report:
  https://www.business-standard.com/cricket/news/india-vs-new-zealand-1st-odi-vadodara-pitch-report-key-stadium-stats-126011000363_1.html
- The Indian Express, India–South Africa Visakhapatnam pitch report:
  https://indianexpress.com/article/sports/cricket/india-vs-south-africa-visakhapatnam-aca-vdca-cricket-stadium-pitch-report-weather-forecast-match-update-10404167/
- The Indian Express, India–South Africa Raipur pitch report:
  https://indianexpress.com/article/sports/cricket/india-vs-south-africa-raipur-shaheed-veer-narayan-singh-international-stadium-pitch-report-weather-forecast-10398416/

Seventeen sixth-batch matches were set aside. The rejected material was
surface-free, generic, ESPN-restricted, published after the scheduled start, or
fantasy/match-prediction content. All 25 working rows record the common collection
instant `2026-09-11T23:53:16Z`; accepted rows separately retain the exact
source-publication and scheduled-start instants. The reviewed match range is
2025-12-03 through 2026-06-04.

## Seventh-batch source release

The seventh 25-match outcome-blind batch was selected newest-first and reviewed
individually on 2026-09-12. Eight non-ESPN reports met the source, timing, and
surface-evidence requirements:

- The Indian Express, India–South Africa Ranchi pitch report:
  https://indianexpress.com/article/sports/cricket/india-vs-south-africa-ranchi-jsca-international-stadium-pitch-report-weather-forecast-match-update-10393073/
- Cricket Addictor, Pakistan–Sri Lanka Rawalpindi third-ODI pitch report:
  https://cricketaddictor.com/cricket-news/pak-vs-sl-weather-report-pitch-report-of-rawalpindi-3rd-odi-sri-lanka-tour-of-pakistan-2025-291362/
- Cricket Times, Pakistan–Sri Lanka Rawalpindi series-opening pitch report:
  https://crickettimes.com/2025/11/pakistan-vs-sri-lanka-2025-rawalpindi-pitch-report-odi-stats-and-records/
- Dawn, Pakistan–South Africa Faisalabad second-ODI preview:
  https://www.dawn.com/news/1953418/pakistan-seek-odi-series-win-as-sa-eye-comeback
- Cricket Addictor, New Zealand–West Indies Napier second-ODI pitch report:
  https://cricketaddictor.com/cricket-news/nz-vs-wi-weather-report-pitch-report-of-mclean-park-napier-2nd-odi-west-indies-tour-of-new-zealand-2025-296615/
- Cricket Times, New Zealand–England Bay Oval first-ODI pitch report:
  https://crickettimes.com/2025/10/nz-vs-eng-pitch-report-for-1st-odi-bay-oval-stats-and-records/
- The Indian Express, Australia–India Sydney third-ODI pitch report:
  https://indianexpress.com/article/sports/cricket/india-vs-australia-3rd-odi-sydney-cricket-ground-pitch-report-weather-update-ind-vs-aus-10324904/
- The Indian Express, Australia–India Adelaide second-ODI pitch report:
  https://indianexpress.com/article/sports/cricket/india-vs-australia-2nd-odi-adelaide-oval-stadium-pitch-report-weather-update-ind-vs-aus-10320531/

Seventeen seventh-batch matches were set aside. The rejected material was absent,
surface-free, generic, ESPN-restricted, or embedded in fantasy, betting, live, or
match-prediction content. All 25 working rows record the common collection instant
`2026-09-12T00:04:35Z`; accepted rows separately retain the exact source-publication
and scheduled-start instants. The reviewed match range is 2025-09-04 through
2025-11-30.

## Eighth-batch source release

The eighth 25-match outcome-blind batch was selected newest-first and reviewed
individually on 2026-09-12. Six non-ESPN reports met the source, timing, and
surface-evidence requirements:

- Cricket Times, England–South Africa Headingley first-ODI pitch report:
  https://crickettimes.com/2025/09/eng-vs-sa-2025-pitch-report-for-the-1st-odi-headingley-stats-and-records/
- Cricket Addictor, Zimbabwe–Sri Lanka Harare first-ODI pitch report:
  https://cricketaddictor.com/cricket-news/zim-vs-sl-weather-report-pitch-report-of-harare-1st-odi-sri-lanka-tour-of-zimbabwe-2025-193054/
- Cricket Addictor, Zimbabwe–Sri Lanka Harare second-ODI pitch report:
  https://cricketaddictor.com/cricket-news/zim-vs-sl-weather-report-pitch-report-of-harare-2nd-odi-sri-lanka-tour-of-zimbabwe-2025-198625/
- The Economic Times, Australia–South Africa Mackay second-ODI pitch report:
  https://economictimes.indiatimes.com/news/sports/aus-vs-sa-2nd-odi-great-barrier-reef-arena-weather-updates-pitch-report-of-australia-vs-south-africa-cricket-match/articleshow/123433652.cms
- The Economic Times, Australia–South Africa Mackay third-ODI pitch report:
  https://economictimes.indiatimes.com/news/sports/aus-vs-sa-3rd-odi-great-barrier-reef-arena-weather-updates-pitch-report-of-australia-vs-south-africa-cricket-match/articleshow/123476506.cms
- CricTracker, England–West Indies Edgbaston first-ODI preview:
  https://www.crictracker.com/cricket-previews/eng-vs-wi-2025-england-vs-west-indies-1st-odi-match-preview/

Nineteen eighth-batch matches were set aside. The rejected material was absent,
surface-free, generic, ESPN-restricted, date-only, post-start, or embedded in
fantasy, betting, or match-prediction content. All 25 working rows record the common
collection instant `2026-09-12T00:13:48Z`; accepted rows separately retain exact
source-publication and scheduled-start instants. The reviewed match range is
2025-05-25 through 2025-09-04.

## Ninth-batch source release

The ninth 25-match outcome-blind batch was selected newest-first and reviewed
individually on 2026-09-12. Ten non-ESPN reports met the source, timing, and
surface-evidence requirements:

- Cricket Times, New Zealand–Pakistan Hamilton second-ODI pitch report:
  https://crickettimes.com/2025/04/nz-vs-pak-2025-2nd-odi-injury-update-pitch-report-and-seddon-park-stats-records/
- InsideSport, New Zealand–Pakistan Napier first-ODI pitch report:
  https://www.insidesport.in/cricket/nz-vs-pak-1st-odi-pitch-report-how-will-the-mclean-park-surface-behave-in-napier/
- The Indian Express, South Africa–New Zealand Lahore semifinal pitch report:
  https://indianexpress.com/article/sports/cricket/sa-vs-nz-pitch-weather-report-semi-final-champions-trophy-2025-match-9868158/
- Mint, Australia–India Dubai semifinal pitch report:
  https://www.livemint.com/sports/cricket-news/champions-trophy-2025-india-vs-australia-semifinal-weather-prediction-today-s-ind-vs-aus-match-dubai-pitch-report-11741065171673.html
- Business Standard, India–New Zealand Dubai group-match pitch report:
  https://www.business-standard.com/cricket/champions-trophy/champions-trophy-ind-vs-nz-pitch-report-and-key-stats-of-dubai-stadium-125030100284_1.html
- The Indian Express, Bangladesh–New Zealand Rawalpindi group-match pitch report:
  https://indianexpress.com/article/sports/cricket/bangladesh-vs-new-zealand-champions-trophy-2025-weather-pitch-9851883/
- The Economic Times, Pakistan–India Dubai group-match pitch report:
  https://economictimes.indiatimes.com/news/sports/ind-vs-pak-pitch-report-champions-trophy-2025-india-vs-pakistan-match-dubai-international-cricket-stadium-pitch-and-weather-today/articleshow/118497966.cms
- India Today, England–Australia Lahore group-match pitch report:
  https://www.indiatoday.in/sports/cricket/story/champions-trophy-cricket-australia-vs-england-aus-vs-eng-lahore-pitch-report-playing-xi-2683625-2025-02-21
- Business Standard, India–Bangladesh Dubai group-match pitch report:
  https://www.business-standard.com/cricket/champions-trophy/champions-trophy-ind-vs-ban-pitch-report-and-key-stats-of-dubai-stadium-125021900679_1.html
- MyKhel, Zimbabwe–Ireland Harare second-ODI preview:
  https://www.mykhel.com/cricket/zim-vs-ire-playing-11-2nd-odi-zimbabwe-vs-ireland-probable-xi-preview-weather-and-pitch-report-341182.html

Fifteen ninth-batch matches were set aside. The rejected material was absent,
surface-free, generic, ESPN-restricted, or embedded in fantasy, live, post-match,
or match-prediction content. All 25 working rows record the common collection
instant `2026-09-12T07:51:50Z`; accepted rows separately retain exact
source-publication and scheduled-start instants. The reviewed match range is
2025-02-16 through 2025-05-21.

## Tenth-batch source release

The tenth 25-match outcome-blind batch was selected newest-first and reviewed
individually on 2026-09-12. Ten non-ESPN reports met the source, timing, and
surface-evidence requirements:

- MyKhel, Sri Lanka–Australia Colombo second-ODI preview:
  https://www.mykhel.com/cricket/sl-vs-aus-playing-11-2nd-odi-sri-lanka-vs-australia-probable-playing-xi-preview-weather-and-pitch-report-340956.html
- MyKhel, Sri Lanka–Australia Colombo first-ODI preview:
  https://www.mykhel.com/cricket/sl-vs-aus-playing-11-1st-odi-sri-lanka-vs-australia-probable-playing-xi-preview-weather-pitch-340463.html
- Business Standard, India–England Ahmedabad third-ODI pitch report:
  https://www.business-standard.com/cricket/news/ind-vs-eng-3rd-odi-pitch-report-and-key-stats-of-narendra-modi-stadium-125021100722_1.html
- MyKhel, New Zealand–South Africa Lahore tri-series pitch report:
  https://www.mykhel.com/cricket/new-zealand-vs-south-africa-weather-and-pitch-report-2nd-odi-gaddafi-stadium-lahore-conditions-for-nz-vs-sa-tri-series-in-pakistan-339940.html
- MyKhel, India–England Cuttack second-ODI pitch report:
  https://www.mykhel.com/cricket/india-vs-england-2nd-odi-ind-vs-eng-pitch-and-weather-forecast-barabati-stadium-report-339857.html
- The Economic Times, India–England Nagpur first-ODI pitch report:
  https://economictimes.indiatimes.com/news/sports/ind-vs-eng-1st-odi-pitch-report-playing-conditions-in-nagpur-what-to-expect/articleshow/117971571.cms
- Cricket Times, New Zealand–Sri Lanka Hamilton second-ODI pitch report:
  https://crickettimes.com/2025/01/nz-vs-sl-hamilton-weather-forecast-for-the-2nd-odi-pitch-report-seddon-park-odi-stats-and-records-new-zealand-vs-sri-lanka-2024-25/
- MyKhel, South Africa–Pakistan Paarl first-ODI pitch report:
  https://www.mykhel.com/cricket/south-africa-vs-pakistan-weather-report-1st-odi-boland-park-pitch-report-and-weather-forecast-on-december-17-327396.html
- InsideSport, West Indies–Bangladesh St Kitts second-ODI pitch report:
  https://www.insidesport.in/cricket/bangladesh-vs-west-indies-warner-park-pitch-report-stats-ahead-of-ban-vs-wi-2nd-odi/
- Cricket Addictor, Australia–Pakistan Perth third-ODI pitch report:
  https://cricketaddictor.com/cricket-news/aus-vs-pak-weather-report-and-pitch-report-of-perth-stadium-3rd-odi-pakistan-tour-of-australia-2024/

Fifteen tenth-batch matches were set aside. The rejected material was absent,
surface-free, generic, ESPN-restricted, later-match, live, post-match, or embedded
in fantasy or match-prediction content. All 25 working rows record the common
collection instant `2026-09-12T07:56:44Z`; accepted rows separately retain exact
source-publication and scheduled-start instants. The reviewed match range is
2024-11-08 through 2025-02-14.

## Eleventh-batch source release

The eleventh 25-match outcome-blind batch was selected newest-first and reviewed
individually on 2026-09-12. One non-ESPN report met the source, timing, and
surface-evidence requirements:

- MyKhel, West Indies–England Barbados third-ODI preview:
  https://www.mykhel.com/cricket/wi-vs-eng-3rd-odi-preview-west-indies-and-england-weather-pitch-report-key-players-injury-updates-318378.html

Twenty-four eleventh-batch matches were set aside. Twenty were qualification-pathway
matches for which no timestamped match-specific surface analysis was located. The
remaining material was surface-free, post-match, or embedded in fantasy, betting,
or match-prediction content. All 25 working rows record the common collection
instant `2026-09-12T08:00:55Z`; the accepted row separately retains exact
source-publication and scheduled-start instants. The reviewed match range is
2024-08-21 through 2024-11-07.

## Twelfth-batch source release

The twelfth 25-match outcome-blind batch prioritized the newest remaining
non-qualification competitions using only queue metadata and was reviewed
individually on 2026-09-12. Twelve non-ESPN reports met the source, timing, and
surface-evidence requirements:

- MyKhel, Sri Lanka–India Colombo third-ODI pitch report:
  https://www.mykhel.com/cricket/ind-vs-sl-3rd-odi-r-premadasa-cricket-stadium-pitch-report-and-colombo-weather-forecast-298947.html
- The Economic Times, Sri Lanka–India Colombo second-ODI pitch report:
  https://economictimes.indiatimes.com/news/sports/india-vs-sri-lanka-pitch-report-2nd-odi-r-premadasa-stadium-columbo-weather-ind-vs-sl-2nd-odi-live-streaming-timing-win-predictor/articleshow/112259141.cms
- Hindi OneIndia, Bangladesh–Sri Lanka Chattogram third-ODI pitch report:
  https://hindi.oneindia.com/news/sports/cricket/bangladesh-vs-sri-lanka-3rd-odi-pitch-and-weather-report-ban-vs-sl-head-to-head-record-900015.html
- Hindi OneIndia, Bangladesh–Sri Lanka Chattogram second-ODI pitch report:
  https://hindi.oneindia.com/news/sports/cricket/bangladesh-vs-sri-lanka-2nd-odi-pitch-and-weather-report-zahur-ahmed-chowdhury-stadium-chattogram-898387.html
- MyKhel, South Africa–India Gqeberha second-ODI pitch report:
  https://www.mykhel.com/cricket/india-vs-south-africa-2nd-odi-st-georges-park-gqeberha-pitch-report-weather-forecast-records-252075.html
- MyKhel, India–Australia Ahmedabad World Cup final pitch report:
  https://www.mykhel.com/cricket/narendra-modi-stadium-ahmedabad-pitch-report-weather-forecast-for-ind-vs-aus-world-cup-2023-final-246105.html
- The Sporting News, South Africa–Australia Kolkata World Cup semifinal pitch report:
  https://www.sportingnews.com/in/cricket/news/australia-south-africa-how-has-eden-gardens-pitch-played-world-cup-2023/495b888f41e0f531e3d82763
- Mint, India–New Zealand Mumbai World Cup semifinal preview:
  https://www.livemint.com/sports/cricket-news/india-v-new-zealand-semifinal-preview-world-cup-2023-predicted-xi-pitch-report-where-to-watch/amp-11699989807751.html
- MyKhel, India–Netherlands Bengaluru World Cup pitch report:
  https://www.mykhel.com/cricket/m-chinnaswamy-stadium-bengaluru-pitch-report-weather-forecast-for-ind-vs-ned-icc-world-cup-2023-244867.html
- MyKhel, England–Pakistan Kolkata World Cup pitch report:
  https://www.mykhel.com/cricket/eden-gardens-kolkata-pitch-report-weather-forecast-for-eng-vs-pak-icc-odi-world-cup-2023-match-44-244735.html
- MyKhel, Australia–Bangladesh Pune World Cup pitch report:
  https://www.mykhel.com/cricket/mca-stadium-pune-pitch-report-weather-forecast-for-aus-vs-ban-icc-odi-world-cup-2023-match-43-244707.html
- MyKhel, New Zealand–Sri Lanka Bengaluru World Cup pitch report:
  https://www.mykhel.com/cricket/m-chinnaswamy-stadium-bengaluru-pitch-report-weather-forecast-for-nz-vs-sl-icc-odi-world-cup-2023-244335.html

Thirteen twelfth-batch matches were set aside. The rejected material lacked an
exact accessible publication timestamp, was source-free, was live or post-match,
or appeared in fantasy or match-prediction content. All 25 working rows record the
common collection instant `2026-09-12T08:05:57Z`; accepted rows separately retain
exact source-publication and scheduled-start instants. The reviewed match range is
2023-11-06 through 2024-08-07.

## Completion batches and provider audit

Batches 13–19 reviewed the final 175 matches needed for the prespecified collection
target. They added 112 verified reports and 63 set-asides:

| Batch | Selection scope | Verified | Set aside |
|---|---|---:|---:|
| 13 | 2023 World Cup | 25 | 0 |
| 14 | 2023 World Cup | 21 | 4 |
| 15 | 2019 World Cup | 18 | 7 |
| 16 | 2019 and 2015 World Cups | 13 | 12 |
| 17 | remaining World Cup, Champions Trophy, and Asia Cup | 13 | 12 |
| 18 | Australia and West Indies tours of India | 9 | 16 |
| 19 | India in South Africa, Sri Lanka in New Zealand, and Australia in England | 13 | 12 |
| **Total** |  | **112** | **63** |

The completion batches used the same source, timing, and surface-evidence gates as
the first twelve batches. Date-only publication values were retained only when the
publisher omitted a time and the local publication date itself preceded the local
match date. Live, post-match, fantasy, betting, match-prediction, generic venue,
surface-free, inaccessible, and syndicated ESPN-labelled pages were set aside
rather than converted into pitch codes. The canonical row-level record—including
every accepted URL, publication value, access timestamp, code, confidence, and
short original paraphrase—is `data/manual/pitch_reports_verified.csv`; every
reviewed rejection and reason is in `data/manual/pitch_set_aside.csv`.

### Post-target expansion batches (20–22)

The same outcome-blind queue and source/timing gates were retained after the
prespecified 200-match target was reached. No separate post-target category was
introduced: all accepted rows enter the same verified pitch and start-time files.

| Batch | Queue slice | Accepted | Set aside |
|---|---|---:|---:|
| 20 | Newest unreviewed 2024–2023 matches | 4 | 21 |
| 21 | June–July 2023 qualifiers and bilaterals | 14 | 11 |
| 22 | March–May 2023 qualifiers and bilaterals | 4 | 21 |
| **Total** |  | **22** | **53** |

Batch 20 used three match-specific Business Standard previews and one NewsBytes
preview. Batch 21 used eight dated Business Standard day previews to code 14
match-specific venue reports. Batch 22 used one Daily Star preview, two Dawn
previews, and one SuperSport preview. Each source URL, publication time, access
time, match linkage, code, confidence, and original short paraphrase is retained in
`data/manual/pitch_reports_verified.csv`.

Across all 22 batches, 222 of 550 reviewed matches have eligible, timing-verified
codes; 328 are explicitly set aside and 544 remain unreviewed. The accepted reports
span 31 normalized provider hostnames. MyKhel contributes 53 matches (23.9%), ICC
36 (16.2%), and Indian Express 23 (10.4%); the top three contribute 51.8%, and the
provider HHI is 1,192. Provider concentration and confidence/category counts are
reproduced in `artifacts/tables/pitch_source_providers.csv` and
`artifacts/tables/pitch_source_provider_audit.json`.
