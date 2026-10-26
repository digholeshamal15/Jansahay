# External data sources and notices

JanSahay uses selected, transformed records from the following public Hugging Face dataset repositories. Both publisher metadata records declare **MIT**. The repository cards provide no separate copyright-holder statement or standalone LICENSE file in the inspected revision; attribution and the declared license are preserved here without inventing one. Publication on Hugging Face alone is not evidence of real citizen provenance.

## Public Grievance Dataset

- Publisher/repository: [hackermango/Public_Grievance_Dataset](https://huggingface.co/datasets/hackermango/Public_Grievance_Dataset)
- Revision: `0f0eba3851e698758bba892c39bdf308c13472dd`
- File: `Public_Grievance_Dataset.csv`
- SHA-256: `a5ef40442cd8beb359cb1b64486023dba05dcd981354e665e975acded7be6577`
- Downloaded rows: 12,500. Selected before deduplication: 1,441.
- Fields used: grievance text, published category/subcategory, department for stripping explicit routing headers, location fields for split grouping. Published priority/status/days_open are not training features or targets.
- Provenance: the dataset card contains only the MIT declaration. The records appear heavily templated; real citizen sourcing is not established.

Label mapping:

| Published subcategory | JanSahay category |
|---|---|
| Pothole or damaged road; Road excavation restoration; Footpath obstruction or damage; Bridge or culvert maintenance; Public works quality or delay | roads |
| Streetlight outage | lights |
| Missed waste collection; Public bin overflow | garbage |
| Drain cleaning; Sewage overflow | drainage |
| Water connection or meter; Water quality concern; Leakage and pipe repair; Irregular water supply | water |

Other subcategories are excluded. In particular, household electricity faults are not relabelled as streetlight complaints and irrigation requests are not relabelled as urban water-supply complaints.

## CivicDex

- Publisher/repository: [JadeSamLee/civicdex](https://huggingface.co/datasets/JadeSamLee/civicdex)
- Revision: `b46543ef1e35936ee713faf008d995fc28abbc1e`
- File: `civicdex_main.csv`; 600 rows. Selected before deduplication: 366.
- SHA-256: `b75934af682fe2275b1147cbdde3bc8b2c3411f685b988ec5ca5a127472f5467`
- Fields used: English gloss and published category; request ID retained for audit.
- Mapping: water_supply → water; sanitation → garbage; street_lighting → lights; drainage → drainage; roads → roads.
- Only the main CSV is used. The adapted CSV is not treated as an independent second dataset.
- The card describes a prototype/seed dataset with synthetic/realistic samples and states that it contains no real citizen data. Row-level source_type labels are not treated as independently verified provenance.
- Original language inputs are Tamil/Tanglish/code-mixed; this project uses the English gloss. There is no native Hindi/Marathi source data here.

CivicDex includes its own row-level train/val/test hints. We build a new group-separated split jointly with Public Grievance, rather than combine their original splits and risk duplicate/core overlap. Consequently our reported benchmark is a **JanSahay-derived split**, not the original CivicDex benchmark.

## Prepared files and reproduction

`data/service_train.json`, `data/service_validation.json` and `data/service_test.json` include source/source_id and complaint-pattern group IDs. `data/dataset_manifest.json` records selected/duplicate counts, the split rule and class/language/source distributions. The original 90 authored examples remain in `data/training.json`, with no claim of external provenance. No source license is claimed to cover the user's future submissions.

The raw CSVs can be downloaded at the exact revisions by `scripts/prepare_hf_data.py`; they are not bundled with all the unrelated upstream categories. The script preserves existing labels and filters them explicitly. It performs no automatic translation and creates no synthetic rows.

## MIT license text (publisher-declared terms)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
