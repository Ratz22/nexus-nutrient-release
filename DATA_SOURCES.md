# NanoFert: Data Sources Registry

Status: **VERIFIED** = I opened the page and confirmed a downloadable data file. **CANDIDATE** = found in search, contents not checked. **IN-PAPER** = real primary data, but only in tables/figures.
Licenses are what the pages stated; re-check before commercial use. Not legal advice.

## A. Downloadable raw data
| ID | Source | Data | License | Status |
|---|---|---|---|---|
| plos_pcu_2020 | Ransom et al., PLOS ONE 2020, doi:10.1371/journal.pone.0234544 | S1 Data (XLSX): N release from urea, SCU, PCSCU, PCU 45/75/120/180 by placement and static vs fluctuating temperature, weekly sampling. NOT nano-scale; use as controlled-release physics benchmark. | CC BY 4.0 | VERIFIED |
| bath_zn_beads_2023 | Univ. of Bath Research Data Archive, doi:10.15125/BATH-01224 | Cellulose acetate microbeads, Zn release (ICP-OES), particle size, soil data (Excel). | CC BY 4.0 on STL file; confirm for xlsx | VERIFIED (landing page) |
| zenodo_23161934 | https://zenodo.org/records/23161934 | Cellulose-ether slow-release fertilizer, N forms at 7/14/21/28 d. | check API output | CANDIDATE |

## B. Nano-fertilizer papers with primary release data in tables/figures
| Paper | ID | Contains | Status |
|---|---|---|---|
| Date-industry-waste nano-fertilizers (P, K, Mg) | PMC10991569 | Release in water and soil, 4 kinetic models | IN-PAPER |
| Drinking-water-waste nano-fertilizers | doi:10.1038/s41598-024-56274-0 | Release kinetics + sorption | IN-PAPER |
| Nitrate-doped Ca-phosphate nanofertilizers | PMC7382453 | Dissolution kinetics vs structure | IN-PAPER |
| Rice-straw cellulose nanofibre urea carrier | doi:10.1080/21655979.2023.2242124 | Release over days; page states a public data repository (see Data Availability) | IN-PAPER + possible repository |
| 15N tracing nano-enabled N | doi:10.1039/D6EN00403B | First-order rate constants | IN-PAPER |
| Nano-biochar PVA/PVP urea matrix | ScienceDirect S2666821125001140 | Mass-transfer and release kinetics | IN-PAPER (access unverified) |
| Nitrogenous nanocomposite, lettuce columns | doi:10.1186/s11671-023-03874-w | Leaching in soil columns, 45 d | IN-PAPER |
| nHAP from biowaste, soil column | PMC11843612 | P release and leaching | IN-PAPER |
| K-doped ACP + urea | PMC13471757 | Column leaching | IN-PAPER |
| ACP/HAP + urea, vermiculite column | PMC12272682 | Urea release in column | IN-PAPER |
| Chitosan-urea / PLGA nano-fertilizers | orientjchem.org vol42no3 | Release fitted to 4 models | IN-PAPER |
| PCU/PCPC cumulative release, cotton | doi:10.1038/srep39030 | Release curves in water/soil | IN-PAPER |

Route for B: extract tables (camelot/pdfplumber), digitize figures (WebPlotDigitizer), and email corresponding authors for raw numbers. Log every point in manual_entry_template.csv.

## C. Checked and rejected
- Kaggle crop/fertilizer recommendation sets: map soil N/P/K to a crop or fertilizer label. No release-over-time data, provenance mostly unstated. Not primary data for this project.
- Patents: contain release tables but are not peer-reviewed and carry IP risk for a commercial product.
- Review articles: useful for finding primary papers, not primary themselves.