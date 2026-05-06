# Olist Logistics Dashboard — Delays & Cancellations Analysis

This repository contains the complete data processing pipeline, interactive dashboard, and final report for the **Control de Retrasos y Cancelaciones en Olist** project. It was developed as the final assignment for the Data Visualization course at Spain Business School (2025/2026).

The goal is to provide logistics and operations teams with a clear, visual tool to monitor the financial impact of late deliveries, identify root causes (by product category and geographic route), and track the effectiveness of corrective actions over time.

## 🗂️ Project Structure

```
.
├── angel-feliz-visializacion-de-datos-final.qmd   # Quarto source of the final report (PDF)
├── angel-feliz-visializacion-de-datos-final.pdf   # Compiled report
├── prepare_dashboard_data.py                      # Python script that builds the unified dataset
├── default.nix                                     # Nix shell definition for reproducibility
├── docker-compose.yml                              # Docker Compose configuration
├── Dockerfile                                      # Docker image definition
├── setup.sh                                        # One‑command setup script (build & run)
├── raw-data/                                       # Original CSV files from Kaggle (unpacked)
├── processed-data/
│   └── orders_processed.xlsx                       # Generated dataset ready for Looker Studio
├── img/                                            # Screenshots and diagrams used in the report
├── context/                                        # Additional reference files (schemas, notes)
└── README.md
```

## 🔍 The Dashboard

An interactive Looker Studio dashboard that tells a data story:

- **Macro indicators**: total cancellation cost, % of delayed orders, satisfaction score.
- **Time series**: monthly cancellation cost and delivery days (on‑time vs. delayed).
- **Root causes**: top delayed categories, heatmap of seller‑customer routes.
- **Drill‑down filters**: by date, product category, and state of seller/customer.

> *Dashboard link: https://datastudio.google.com/reporting/6ca33c99-f68c-49aa-b22e-1023320fabdd*

![](img/01-dashboard-general.jpg)

## 📊 Data Source

The dataset used is the public [Brazilian E‑Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) available on Kaggle.  
It contains information about 100k+ orders, customers, sellers, products, and reviews from the Olist marketplace between 2016 and 2018.

## 🐍 Data Processing

The script `prepare_dashboard_data.py` performs the following steps:

1. Loads the 9 original CSV files from `raw-data/`.
2. Enriches products with derived attributes (volume, category grouping).
3. Aggregates orders to a single row per order, merging customer, seller, and review data.
4. Computes logistic indicators: delay days, handling/transit times, cancellation cost, margin.
5. Exports the final table `orders_processed.xlsx` (99,441 rows × 37 columns) that feeds the dashboard.

## 🚀 Getting Started

The development environment is fully reproducible using Nix and Docker, guaranteeing consistent dependencies across machines.

### Option 1: Docker (recommended)

```bash
# Clone the repository
git clone https://github.com/AngelFelizR/olist-logistics-dashboard.git
cd olist-logistics-dashboard

# Run the one‑click setup
chmod +x setup.sh
./setup.sh
```

The setup script:

- Builds the Docker image (Nix environment inside).
- Starts the container with SSH access on port 2225.
- Injects your public SSH key for password‑less connection.

After that, you can connect via:

```bash
ssh root@localhost -p 2225
```

Inside the container, the project is mounted at `/root/olist-logistics-dashboard`.  
To regenerate the dataset, run:

```bash
python prepare_dashboard_data.py
```

The processed file will be saved under `processed-data/orders_processed.xlsx`.

### Option 2: Nix directly (if Nix is installed)

```bash
nix-shell default.nix --run "python prepare_dashboard_data.py"
```

## 📝 Final Report

The project report (`angel-feliz-visializacion-de-datos-final.pdf`) is generated from the Quarto markdown file.  
To recompile it (inside the Nix/Docker environment):

```bash
quarto render angel-feliz-visializacion-de-datos-final.qmd --to pdf
```

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Olist](https://www.olist.com/) for releasing the dataset.
- [Kaggle](https://www.kaggle.com/) for hosting the data.
- Prof. Jorge Valtuena for the guidance and the Data Visualization course framework.

---

*Developed by Ángel Esteban Féliz Ferreras • MSc in Data Science • Spain Business School 2026*