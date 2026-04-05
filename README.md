# 🤖 Prediction Bot — Polymarket NYC Weather

[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

A Python script that scans active **NYC temperature markets on Polymarket**, fetches real weather forecasts via the **Open-Meteo API**, and identifies which market outcome has the smallest edge against the predicted temperature.

---

## 🌐 How It Works

1. **Scrape** — `scraper.py` queries the [Polymarket Gamma API](https://gamma-api.polymarket.com/events) for active events tagged as `weather`.
2. **Parse** — `parser.py` filters only **NYC max temperature** markets and extracts the unit (Celsius or Fahrenheit) from the event slug.
3. **Forecast** — `weather.py` calls the [Open-Meteo](https://open-meteo.com/) free API and returns the forecasted max temperature for the market's end date.
4. **Decide** — `decision.py` compares the forecast against each market's price range and ranks them by proximity — the closer the predicted temperature is to a range, the better the market.
5. **Output** — `main.py` ties everything together and prints the best and second-best market options to the terminal.

---

## 🚀 Features

- Fetches up to 300 active weather markets from Polymarket in a single call.
- Filters exclusively for **NYC max temperature** markets.
- Parses market price ranges via regex (e.g. `72–75°F`, `80°F or higher`, `65°F or below`).
- Retrieves daily max temperature forecasts from Open-Meteo — no API key required.
- Ranks markets by how close the forecast is to each price band.

---

## 🛠️ Tech Stack

| Library | Purpose |
|---|---|
| [requests](https://docs.python-requests.org/) | HTTP calls to Polymarket API |
| [openmeteo-requests](https://pypi.org/project/openmeteo-requests/) | Open-Meteo weather API client |

---

## 📋 Prerequisites

- Python **3.8+**
- No API keys required — both Polymarket Gamma API and Open-Meteo are free and public.

---

## 🔧 Installation & Setup

1. **Clone the repository:**

```bash
git clone https://github.com/Gu1lz/prediction-bot-telegram.git
cd prediction-bot-telegram
```

2. **Install dependencies:**

```bash
pip install requests openmeteo-requests
```

3. **Run:**

```bash
python main.py
```

The script will fetch active NYC weather markets, retrieve the temperature forecast, and print the ranked market outcomes to stdout.

---

## 📂 Project Structure

```
prediction-bot-telegram/
├── main.py        # Entry point — orchestrates the full pipeline
├── scraper.py     # Fetches active weather events from Polymarket Gamma API
├── parser.py      # Filters NYC max temperature markets and extracts the unit
├── weather.py     # Queries Open-Meteo for the forecasted max temperature
├── decision.py    # Ranks markets by proximity of forecast to each price range
├── final.py       # (auxiliary)
└── README.md
```

---

## 🤝 Contributing

1. Fork the project.
2. Create your feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add some AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request.

---

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Developed with ☕ by [Gu1lz](https://github.com/Gu1lz)
