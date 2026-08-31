# LLM Extraction Scorecard

## Overview

The **LLM Extraction Scorecard** evaluates how accurately a large language model can extract financial metrics from SEC filings for publicly traded oil and gas companies.

The project focuses on three metrics:

* **Revenue**
* **Production**
* **Capital Expenditures (CapEx)**

The goal was to determine how reliably an LLM can identify the correct financial value, unit, and reporting period from company filings.

## Companies and Filings

The benchmark uses SEC filings from five oil and gas companies:

* Diamondback Energy (FANG)
* Permian Resources (PR)
* Matador Resources (MTDR)
* Coterra Energy (CTRA)
* SM Energy (SM)

The dataset contains **15 filings**, with three metrics evaluated for each filing, producing **45 total benchmark questions**.

The benchmark includes:

* 10-K filings for fiscal year 2025
* Q1 2026 10-Q filings
* Q2 2026 10-Q filings
* Q3 2025 10-Q filings where applicable

## Metrics

### Revenue

Revenue was primarily taken from the companies' **Consolidated Statements of Operations**.

### Production

Production was taken from the companies' **Production Data**, **Results of Operations**, or equivalent production tables.

The benchmark uses **period production totals**, not average daily production.

### Capital Expenditures

CapEx was taken from the companies' **Statements of Cash Flows** or relevant capital expenditure disclosures.

The benchmark specifically evaluates the capital expenditure figure identified in the answer key rather than other related CapEx measures that may appear elsewhere in a filing.

## Methodology

For each filing:

1. The SEC filing was collected and converted into a text file.
2. The correct answers were independently recorded in an answer key.
3. The filing text was provided to Gemini with a prompt asking it to extract Revenue, Production, and CapEx.
4. Gemini's responses were saved in the `results/` directory.
5. A Python scoring script compared the extracted values against the answer key.
6. Values were normalized when necessary to account for differences in units such as millions, thousands, MBOE, and MMBOE.
7. The final results were calculated across all 45 benchmark questions.

The answer key was verified against the original filings before being used for scoring.

## Results

### Initial Results

The initial extraction results showed significant problems with Revenue and Production extraction.

The initial accuracy was:

* **Revenue:** 4/15 (26.7%)
* **Production:** 0/15 (0%)
* **CapEx:** lower than the final result

### Improvements

The extraction prompt and scoring process were revised to make the requested metrics and reporting periods clearer.

In particular, the improved approach emphasized:

* Extracting the requested metric rather than a related metric
* Distinguishing period totals from average daily values
* Avoiding daily production values when the benchmark required period production
* Providing an exact amount and unit
* Handling different financial units consistently
* Comparing extracted values against independently verified answer-key values

These changes substantially improved Revenue and Production extraction.

### Final Results

The final benchmark achieved **40/45 correct (88.9%)**.

| Metric      |   Correct |   Accuracy |
| ----------- | --------: | ---------: |
| Revenue     |     15/15 | **100.0%** |
| Production  |     15/15 | **100.0%** |
| CapEx       |     10/15 |  **66.7%** |
| **Overall** | **40/45** |  **88.9%** |

Revenue and Production both reached 100% accuracy after the prompt and extraction improvements.

CapEx remained the most difficult metric, accounting for all five remaining errors.

## CapEx Failure Analysis

The five remaining errors were concentrated entirely in CapEx.

### Failure Taxonomy

| Failure Category                                              | Number of Errors |
| ------------------------------------------------------------- | ---------------: |
| Selected a different valid or closely related CapEx component |                4 |
| Failed to identify the correct three-month period             |                1 |

Four of the five errors occurred when Gemini selected a different capital expenditure figure from the filing rather than the specific CapEx figure defined in the answer key.

The remaining error occurred when Gemini concluded that the requested three-month CapEx figure was not explicitly reported, even though the relevant value could be identified from the filing.

This suggests that the primary difficulty with CapEx was **distinguishing among multiple related capital expenditure figures and reporting periods**, rather than simply locating the term "capital expenditures."

## Scoring

The scoring script:

* Extracts the `Exact Amount` and `Unit` from each Gemini response
* Converts financial values to a common dollar scale
* Converts production values to a common MBOE scale
* Rejects daily production values when period production is required
* Allows a small rounding tolerance for financial values
* Compares each extraction against the answer key
* Produces an overall score and metric-level scores

The detailed results are saved in:

`results/detailed_results.csv`

## Repository Structure

```text
llm-extraction-scorecard/
│
├── answer_key/
│   └── answer_key.csv-2.xlsx
│
├── results/
│   ├── *_result.txt
│   └── detailed_results.csv
│
├── src/
│   └── extract.py
│
├── score.py
├── convert_filings.py
├── README.md
└── [filing text files]
```

## Running the Project

### 1. Clone the repository

```bash
git clone https://github.com/aanyag28/llm-extraction-scorecard.git
cd llm-extraction-scorecard
```

### 2. Install dependencies

The project uses Python and the following main libraries:

```bash
pip install openpyxl
```

Additional dependencies required by the extraction script should be installed as specified in the source code.

### 3. Run the extraction

Run the extraction script:

```bash
python3 src/extract.py
```

The script processes the filing text and saves the model's extraction results.

### 4. Run the scoring script

After the extraction results have been generated:

```bash
python3 score.py
```

The scoring script compares the model's answers against the answer key and prints the results.

## Interpreting the Results

The final score of **88.9%** means that Gemini correctly extracted the benchmarked financial metric in **40 of 45 cases**.

The results also show that accuracy depends heavily on the type of metric being extracted.

* **Revenue:** highly reliable after the prompt improvements
* **Production:** highly reliable after clarifying that period totals were required
* **CapEx:** substantially more difficult because filings contain multiple related CapEx figures and reporting periods

The benchmark therefore demonstrates that an LLM can perform highly accurate financial extraction when the requested metric and reporting requirements are clearly defined, while also showing specific limitations in distinguishing closely related CapEx measures.

## Future Work

Potential improvements for a future version of the benchmark include:

* Expanding the number of companies and filings
* Testing additional financial metrics
* Comparing multiple LLMs
* Testing whether more explicit instructions about CapEx line items improve accuracy
* Examining whether table structure and formatting affect extraction accuracy
* Expanding the CapEx failure taxonomy with a larger dataset

## Conclusion

The final benchmark achieved **88.9% overall accuracy**, with Revenue and Production reaching **100% accuracy**.

The remaining errors were entirely concentrated in CapEx, providing a useful finding rather than simply a lower score. Most CapEx errors resulted from the model selecting a different but related capital expenditure figure, highlighting the difficulty of extracting financial information when filings contain multiple similar measures.

The project demonstrates both the strengths of LLM-based financial extraction and the importance of precise metric definitions, reporting-period requirements, and independently verified benchmark answers.
