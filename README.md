# 🏪 Multi-Outlet Shop Analytics App

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red?style=flat-square&logo=streamlit)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey?style=flat-square&logo=sqlite)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange?style=flat-square&logo=scikit-learn)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

> AI-powered billing, stock & revenue analytics for shops with multiple outlets — built to replace traditional software like Tally with a smarter, real-time dashboard.

🔗 **Live App:** [shopanalyticsapp.streamlit.app](https://shopanalyticsapp.streamlit.app/)

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 🔐 **Auth & Roles** | Owner sees all outlets; Manager sees only their own |
| 🧾 **Smart Billing** | Add items to cart, auto stock deduction on bill generation |
| 📦 **Inventory** | Real-time stock tracking with low-stock alerts & restock |
| 📊 **Revenue Dashboard** | Daily trends, top items, payment mode split (Plotly charts) |
| 🤖 **AI Recommendations** | Session-wise top sellers + next-day demand forecast (Linear Regression) |
| 🏬 **Outlet Comparison** | Owner-only side-by-side multi-outlet analytics |

---

## 🛠️ Tech Stack

- **Frontend & Backend** — Streamlit
- **Database** — SQLite
- **Data Analysis** — Pandas, NumPy
- **Visualizations** — Plotly
- **Machine Learning** — scikit-learn (Linear Regression, session clustering)

---

## 🚀 Setup & Installation

```bash
# 1. Clone the repository
git clone https://github.com/harshdharmik29/shop-analytics-app.git
cd shop-analytics-app

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database & run
python database.py
streamlit run app.py
```

> The database (`data/shop.db`) and sample data are created automatically on first run.

---

## 🔐 Default Login Credentials

| Role | Username | Password | Access |
|------|----------|----------|--------|
| Owner | `admin` | `admin123` | All outlets |
| Manager | `manager1` | `manager123` | Outlet 1 only |

> ⚠️ **Change these credentials before deploying to production.**

---

## 📁 Folder Structure

```
shop_analytics_app/
├── app.py                      # Main entry / login page
├── database.py                 # DB connection + table creation
├── utils.py                    # Helper functions (auth, calculations)
├── pages/
│   ├── 1_Dashboard.py          # Revenue analysis & charts
│   ├── 2_Billing.py            # Bill entry + auto stock deduction
│   ├── 3_Inventory.py          # Stock management + low-stock alerts
│   ├── 4_Recommendations.py    # Session-wise AI recommendations
│   └── 5_Outlet_Comparison.py  # Owner-only multi-outlet view
├── ml/
│   ├── demand_forecast.py      # Next-day demand prediction
│   └── session_analysis.py     # Hour/day-wise top item clustering
├── data/
│   └── shop.db                 # SQLite database (auto-created)
└── requirements.txt
```

---

## 📝 Notes

- This app is intended for **private/internal use** (owner + outlet staff only).
- On Streamlit Community Cloud, enable **Viewer Authentication** under app Settings → Sharing to restrict access.
- To add more outlets or users, use [DB Browser for SQLite](https://sqlitebrowser.org/) to edit `data/shop.db` directly.
- AI recommendations improve as more billing data accumulates — generate a few days of bills to see meaningful results.

---

## 👤 Author

**Harsh Dharmik**
- 🐙 GitHub: [@harshdharmik29](https://github.com/harshdharmik29)
- 💼 LinkedIn: [in/harshdharmik](https://linkedin.com/in/harshdharmik)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
