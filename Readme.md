# Investment Highlights (Mainframe)

## Overview
Starting as a DevOps practice yard, this project evolved into an end-to-end Data Analysis project.
Initial commits were to practice with DevOps tools, but the project evolved over time to be more of a DIY Data Engineering Pipeline that fueled securities analysis projects. The insights found from this data may be found at investmenthighlights.com at the discretion of the site host.

---
jenkinsFiles and k8-yamls were initial commits, representing orchestration of the project and self-hosted CI/CD tool(s). They were unused in the Data Analysis and Engineering portions of the project.

---
../mainframe contains the DIY data pipeline, connecting to the SEC's EDGAR API to collect securities data. That data is cleaned in Mega.py and loaded into the SQLite3 DB. Mega-related cleaning involves basic financial statement data, parsing it from the json files from EDGAR and organizing it into a tabular format within SQLite.

**Essentially, Mega.py is a DIY ETL.** 

Metadata.py takes data from the DB, and produces metadata related to securities analysis, inserting these new values into the same DB. These metadata include averages of all kinds, and more advanced financial metrics such as ROIC, profit margins, etc.

Together, these two .py-files populate the DB with production-level data that can be used to glean insights for a variety of financially-related uses.

## Future Directions
Future additions to this project are taking most of the work done in Mega.py and refactoring it to include Apache Airflow, to bring the ETL pipeline into a more industry-standard form.

The infrastructure running investmenthighlights.com desperately needs monitoring added to it. As well as Ansible playbooks set to a cron job to keep that infrastructure up to date.

Currently, docker-compose is contained on the same instance that runs the website and could be moved externally to manage not just that instance, but an entire ecosystem of infrastructure; post revisions, of course.

### ETL -> ELT
First, Airflow will orchestrate the transformation of the project into ELT instead of ETL, storing raw(Bronze level) data in an AWS S3 bucket. This step will run every six months, checking each CIK (a ticker identifier used by the SEC's EDGAR) against data that is already stored in the S3 bucket using a hash value attached to each stored json file. If new json-hashes match what's already stored, no new json is saved to S3, and vice versa, including a title change to reflect the latest date of data saved. 

This removes redundant data storage, while also adding an auditable trail for each ticker's raw data. This step is currently skipped by Mega.py and would add enormous value for not only data audits, but for lowering costs, making data queries for raw data faster and cheaper, local, rather than having to query EDGAR with each new data pondering.

The same S3 bucket, minimizing costs in architectural design, will also contain Silver level data, Parquet-ized cleaned data from the Bronze level, cleaned and stored there by processes triggered by Apache Airflow. If a CIK/ticker were updated at the bronze level, this would trigger Airflow to update the Silver level data by adding a newer-dated Parquet entry. 
This process now is in Mega.py and bypasses Bronze level storage altogether, see above, and would essentially be synonymous with a Dev-Env-level database for Analysts to query and generate reports from.

Given how this data is currently displayed on investmenthighlights.com, using a simple SQLite DB that requires only reads from the Django server running the site, if this architecture remains unchanged, Airflow could also trigger a SQLITE3.db update every six months, assuming new data exists, to update the PROD DB that gets distributed with the website's CI/CD pipeline.

## InvestmentHighlights.com Future Plans
Disclaimer: I am not a Front-End Engineer... and it shows. 

Initial iterations of IH.com show breakdowns of the three financial statements, as well as some other data gathered in this project, but many steps can be taken to make the insights therein more digestible for human readers. The use of graphs rather than tabular data would go a long way to making the site more intuitive for users.

Some samples of graphed data produced so far (By navCheck.py only) may be found in Mainframe/mainframe/, but for specific data related to what's already on IH.com, more work needs to be done.

## Mainframe/mainframe/investor_center
Multiple .py files here represent past and currently ongoing projects related to financial analysis.

Mega.py and Metadata.py are used to query data from the SEC, clean it, organize it into usefulness to be uploaded into the Django-Prod DB.

navCheck.py contains nifty tools to compare two funds, originally used to compare covered call funds versus their underlying targets. In its current iteration, one selects what timeline to test over, and four graphs are produced. Graph 1 shows price returns of the two funds. Graph 2 shows total returns. Graph 3 shows a normalized comparison of the two funds' price actions, the first fund against the second. How does the tested funds' price action capture movement of the underlying? You want to see this graph be flat at 1 continuously, or preferably sloping upward. Covered call funds tend to trend downward int his graph during steep bull markets. Graph 4 shows the distributions from both funds, given the same amount of money invested into either holding.
Diagrams of some sample outputs from this can be found at Mainframe/mainframe.

SectorRankings.py is a deprecated feature of investmenthighlights.com, most likely to be added later, ranking different GICS sectors based on multiple of their respective financial metrics. ROA in Financials for example, ROIC for others, Book Value per share in REIT's and BDC's, etc. 

Valuation.py takes lists of tickers and then runs DDM models on them, comparing expected returns over the next five years. It also lists the tickers in a second returned table based on current valuations of Price / Dividend, measuring exactly what your return, in in-hand cash, would be per dollar spent to purchase the fund/stock/etc. This .py file is the beginning of a valuation tool project to analyze comparisons of the above metrics versus actual returns historically. 

Unused Currently: altTables.py


## Final Notes
A lot of the code needs cleaning up. Obviously, refactoring the project to include Apache Airflow will take time, but the improvements of ETL -> ELT will vastly improve the data integrity of the project.
Over time, the data analysis tools to glean financial insights won't just be a fun toy, rather becoming tools that I can use personally, or help others to educate themselves financially.