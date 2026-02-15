<a name="readme-top"></a>

[![Python][Python-shield]][Python-url]
[![GitHub Actions][Actions-shield]][Actions-url]
[![Telegram][Telegram-shield]][Telegram-url]
[![MIT License][license-shield]][license-url]


<br />
<div align="center">
  <h3 align="center">SJ Night Train Watchdog</h3>

  <p align="center">
    A dedicated, automated bot that monitors SJ.se for specific Night Train tickets and alerts you via Telegram the moment they are released.
    <br />
    <br />
    <a href="#usage">View Demo</a>
    ·
    <a href="https://github.com/othneildrew/Best-README-Template/issues">Report Bug</a>
    ·
    <a href="https://github.com/othneildrew/Best-README-Template/issues">Request Feature</a>
  </p>
</div>


<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#features">Features</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>


## About The Project

Finding tickets for the popular **SJ Night Trains** (especially to the north, like Gällivare or Kiruna) can be incredibly difficult. Release dates are unpredictable, the website doesn't offer waitlists, and tickets often sell out immediately upon release.

This **SJ Night Train Watchdog** is a "set it and forget it" solution. It runs automatically in the cloud every morning, acting as your personal travel agent.

It doesn't just check if a train exists in the schedule; it performs a deep inspection to verify:
1.  Is the **Night Train** (07:30 - 09:00 arrival) listed?
2.  Are tickets actually **bookable** (not "Sold Out" or "Blocked")?
3.  What is the current **price**?

If all checks pass, it sends an instant notification to your phone.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Built With

* [![Python][Python-shield]][Python-url]
* [![GitHub Actions][Actions-shield]][Actions-url]
* [![Telegram][Telegram-shield]][Telegram-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Getting Started

To get this up and running, you don't need a server. This project runs entirely on **GitHub Actions** (for free).

### Prerequisites

You need a destination for the alerts. We use **Telegram** because it's fast and free.

1.  **Create a Telegram Bot:**
    * Open Telegram and search for **@BotFather**.
    * Send the message `/newbot`.
    * Follow the steps to name your bot.
    * **Copy the API Token** (It looks like `123456:ABC-DEF1234...`).

2.  **Get Your Chat ID:**
    * Search for **@userinfobot** in Telegram and click Start.
    * **Copy your "Id"** (It is a number like `123456789`).

### Installation

1.  **Fork** this repository.
2.  Go to your repository **Settings** > **Secrets and variables** > **Actions**.
3.  Click **New repository secret** and add these two secrets:
    * `TELEGRAM_BOT_TOKEN`: Paste your Bot Token.
    * `TELEGRAM_CHAT_ID`: Paste your Chat ID.
4.  Open `train_watchdog.py` and configure your trip:
    ```python
    DATE = "2026-08-20"          # Your travel date
    ORIGIN_ID = "740000556"      # Arlanda Central (Default)
    DESTINATION_ID = "740000254" # Gällivare C (Default)
    ```
5.  Commit your changes.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Usage

The Watchdog is designed to run automatically, but you can also control it manually.

### 🔄 Automatic Schedule
The script is configured to run **daily at 08:00 UTC**. You can change this in `.github/workflows/main.yml`.

### ⚡ Manual Trigger
Want to check right now?
1.  Go to the **Actions** tab in your repository.
2.  Select **Run SJ Watchdog** from the list.
3.  Click the **Run workflow** button.

### 🧪 Testing Telegram
To ensure your alerts are working:
1.  Edit `train_watchdog.py`.
2.  Set `TEST_TELEGRAM = True`.
3.  Run the workflow manually. You should receive a "Test Message" immediately.
4.  **Important:** Set it back to `False` afterwards.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Features

- [x] **Targeted Filtering:** Specifically ignores day trains and hunts only for the Night Train (arrival window 07:30 - 09:00).
- [x] **Deep Validation:** Checks specific "Availability" flags in the API to avoid false positives on sold-out trains.
- [x] **Maintenance Detection:** Captures and logs warning codes (e.g., `POTENTIAL_MAINT`) if the train is visible but blocked.
- [x] **Weekly Heartbeat:** Sends a "Still looking..." message every Monday so you know the bot is alive and hasn't crashed.
- [x] **Sanity Checks:** Can be configured to print all trains found in the logs for debugging.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/othneildrew/Best-README-Template/blob/master/LICENSE.txt
[Python-shield]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://python.org
[Actions-shield]: https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white
[Actions-url]: https://github.com/features/actions
[Telegram-shield]: https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white
[Telegram-url]: https://telegram.org