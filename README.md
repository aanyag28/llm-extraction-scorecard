# LLM Extraction Scorecard

## Overview

This project evaluates how accurately a large language model (LLM) can extract financial metrics from SEC filings for publicly traded oil and gas companies.

The benchmark focuses on three metrics:

* **Revenue**
* **Production**
* **Capital Expenditures (CapEx)**

The project uses 15 SEC filings from five Permian Basin oil and gas companies:

* Diamondback Energy (FANG)
* Permian Resources (PR)
* Matador Resources (MTDR)
* Coterra Energy (CTRA)
* SM Energy (SM)

Each filing has a manually verified answer key based directly on the original SEC filing. Gemini's extracted values are compared against that answer key to calculate an accuracy score.

---

## Final Results

| Metric      | Correct |  Total |   Accuracy |
| ----------- | ------: | -----: | ---------: |
| Revenue     |      15 |     15 | **100.0%** |
| Production  |      15 |     15 | **100.0%** |
| CapEx       |      10 |     15 |  **66.7%** |
| **Overall** |  **40** | **45** |  **88.9%** |

Revenue and Production were extracted correctly in every test case. All five remaining errors occurred in CapEx extraction.

---

## Project Structure

```text
LLM-Extraction-Scorecard/
│
├── answer_key/
│   └── answer_key.csv-2.xlsx
│
├── filings/
│   └── Original SEC filing HTML files
│
├── results/
│   ├── Gemini extraction result files
│   └── detailed_results.csv
│
├── src/
│   └── extract.py
│
├── convert_filings.py
├── score.py
├── README.md
│
└── *.txt
    └── Text versions of the SEC filings
```

### Important files

**`answer_key/answer_key.csv-2.xlsx`**
Contains the manually verified ground-truth values for each filing and metric.

**`src/extract.py`**
Contains the extraction workflow used to process the filings and obtain the requested financial metrics.

**`score.py`**
Compares Gemini's extracted values against the answer key and calculates the final accuracy scores.

**`results/detailed_results.csv`**
Contains the final row-by-row comparison between Gemini's extraction and the answer key.

**`filings/`**
Contains the original HTML versions of the SEC filings used in the benchmark.

**`.txt` filing files**
Text versions of the filings used for extraction.

---

## Dataset

The benchmark contains 15 filings across five companies.

| Company            | Ticker | Filings                               |
| ------------------ | ------ | ------------------------------------- |
| Diamondback Energy | FANG   | 2025 10-K, Q1 2026 10-Q, Q2 2026 10-Q |
| Permian Resources  | PR     | 2025 10-K, Q1 2026 10-Q, Q2 2026 10-Q |
| Matador Resources  | MTDR   | 2025 10-K, Q3 2025 10-Q, Q1 2026 10-Q |
| Coterra Energy     | CTRA   | 2025 10-K, Q3 2025 10-Q, Q1 2026 10-Q |
| SM Energy          | SM     | 2025 10-K, Q1 2026 10-Q, Q2 2026 10-Q |

Each filing contributes three test cases: one for Revenue, one for Production, and one for CapEx.

This produces:

**15 filings × 3 metrics = 45 total test cases**

---

## Methodology

### 1. Collect SEC filings

SEC filings were collected for the five companies and converted into text files for use in the extraction process.

### 2. Build the answer key

For every filing, the correct value for Revenue, Production, and CapEx was identified directly from the original filing.

The answer key records:

* Company
* Ticker
* Filing
* Metric
* Value
* Unit
* Page
* Section/Table
* Exact quote or source line

The answer key was independently checked against the filings rather than being based on Gemini's outputs.

### 3. Run Gemini extraction

Gemini was given the filing text and instructed to identify the requested metric.

The extraction process records the model's:

* Extracted value
* Unit
* Relevant metric section

### 4. Normalize values

Because companies report financial values using different units, the scoring script normalizes values before comparing them.

For example:

* Million dollars → dollars
* Thousand dollars → dollars
* MBOE → standardized production units
* MMBOE → standardized production units

This allows equivalent values reported using different scales to be compared fairly.

### 5. Score the results

Each extracted value is compared with the independently verified answer key.

The scoring script produces:

* Per-row correctness
* Accuracy by metric
* Overall accuracy
* `results/detailed_results.csv`

---

## Prompt Improvement

The initial extraction results showed substantial problems with Revenue and Production.

After improving the extraction prompt to make the requested reporting period and metric definitions more explicit, performance improved substantially.

The final results were:

* **Revenue: 100%**
* **Production: 100%**
* **CapEx: 66.7%**
* **Overall: 88.9%**

This improvement suggests that clearer instructions about the target metric and reporting period can significantly improve LLM extraction accuracy from financial filings.

---

## Failure Analysis

All five remaining errors occurred in CapEx extraction.

### Category 1: Different valid CapEx component

In some cases, Gemini identified a legitimate capital expenditure figure, but it did not match the specific CapEx line selected for the benchmark.

**Example — MTDR 2025 10-K**

* Gemini: **$2,155,429,000**
* Answer key: **$1,542,253,000**

Gemini selected a different capital expenditure figure from the filing rather than the specific benchmark line item.

---

### Category 2: Different reporting period

Gemini sometimes selected a CapEx value from a different reporting period than the benchmark required.

**Example — MTDR Q3 2025 10-Q**

* Gemini: **$643,357 thousand**
* Answer key: **$1,093,010 thousand**

The filing contains multiple CapEx figures corresponding to different periods, making period selection an important source of error.

**Example — MTDR Q1 2026 10-Q**

* Gemini: **$496,926 thousand**
* Answer key: **$377,375 thousand**

Again, Gemini selected a different reported CapEx value rather than the benchmark's target value.

---

### Category 3: Different valid CapEx definition

CapEx can be reported using different definitions or aggregations within the same filing.

**Example — CTRA 2025 10-K**

* Gemini: **$2,318 million**
* Answer key: **$2,288 million**

Both values relate to capital expenditures, but Gemini selected a different CapEx figure from the filing than the specific benchmark line.

---

### Category 4: Table/period could not be cleanly parsed

In one case, Gemini did not identify a specific three-month CapEx value.

**Example — CTRA Q3 2025 10-Q**

* Gemini: **"Not explicitly reported for the three-month period"**
* Answer key: **$1,707 million**

This indicates that the model had difficulty interpreting the table structure and identifying the correct reporting period.

---

## Key Finding

The benchmark shows a clear difference between the three metrics.

Revenue and Production were extracted with **100% accuracy**, while CapEx achieved **66.7% accuracy**.

This suggests that CapEx is substantially more difficult to extract consistently because companies can present capital expenditures in different ways, including different line items, definitions, aggregations, and reporting periods.

The remaining errors therefore appear to be concentrated in **interpretation of financial statement structure**, rather than a general inability to locate financial information.

---

## Limitations

This benchmark has several limitations:

* The dataset contains only 15 filings.
* It covers five companies within the oil and gas industry.
* Only three financial metrics were evaluated.
* The benchmark evaluates one LLM and one extraction setup.
* Some filings contain multiple valid-looking values for the same general metric.
* The answer key depends on selecting a specific benchmark definition of each metric.

A larger dataset across more industries, companies, filing types, and financial metrics would provide a stronger measure of general LLM extraction performance.

---

## Reproducing the Project

Clone the repository and enter the project directory:

```bash
git clone https://github.com/aanyag28/llm-extraction-scorecard.git
cd llm-extraction-scorecard
```

Install the required Python dependencies used by the project.

The main workflow consists of:

1. Preparing the SEC filing text files.
2. Running the extraction process in `src/extract.py`.
3. Reviewing the generated Gemini result files in `results/`.
4. Running `score.py` to compare the extracted values against the answer key.
5. Reviewing the final results in `results/detailed_results.csv`.

The answer key in `answer_key/answer_key.csv-2.xlsx` provides the ground-truth values used for scoring.

---

## Conclusion

The final benchmark achieved an overall extraction accuracy of **88.9% (40/45)**.

The model successfully extracted every Revenue and Production value in the benchmark. The remaining errors were concentrated entirely in CapEx, where differences in line-item definitions, reporting periods, and financial statement structure made extraction more difficult.

The results demonstrate that LLMs can perform highly accurate financial metric extraction from SEC filings when the extraction task and reporting period are clearly specified, while also showing that ambiguous financial statement structures remain an important challenge.
