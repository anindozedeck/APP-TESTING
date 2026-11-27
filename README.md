# ReplyWell

**Live app:** https://replywell.onrender.com

ReplyWell is an AI-assisted customer reply draft tool for small businesses in Nairobi, Kenya. Staff paste a customer complaint, generate a calm and professional reply, review it, personalize it, and copy it for use in their support channel.

The app sends complaint text to Anthropic for drafting. Do not enter payment details, passwords, or other sensitive customer information.

## Project package

- **Product:** ReplyWell AI Customer Reply Assistant
- **Target users:** Shops, couriers, Airbnb hosts, restaurants, and other small businesses
- **Core stack:** Python, Flask, Gunicorn, Anthropic Messages API
- **Source entry point:** `Day20_exercise.py`
- **Automated tests:** `test_app.py`
- **Deployment template:** `render.yaml`
- **User walkthrough:** `WALKTHROUGH.md`
- **Client handoff message:** `DELIVERY_MESSAGE.md`
- **Invoice template:** `INVOICE.md`

## Features

- 4,000-character complaint limit
- Required-field and JSON payload validation
- AI-generated drafts that acknowledge the issue and suggest a clear next step
- Provider retry handling for transient network and HTTP failures
- Clear service and network error messages
- Clipboard copy for the generated draft
- Request and provider logging without logging complaint text

## Project structure

```text
Day20_exercise.py  Flask application and Anthropic integration
templates/         HTML page template
static/app.js      Form, loading, error, and clipboard behavior
static/style.css   Responsive interface styles
test_app.py        Flask and provider behavior tests
render.yaml        Render Blueprint deployment configuration
requirements.txt   Python dependencies
README.md          Project and setup documentation
WALKTHROUGH.md     One-page staff usage guide
DELIVERY_MESSAGE.md Ready-to-send delivery handoff
INVOICE.md         Invoice template for the one-time build
```

## Run locally

### Prerequisites

- Python 3.12 or later
- An Anthropic API key
- Internet access for reply generation

### Setup

From the project directory:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the project root:

```dotenv
ANTHROPIC_API_KEY=your_key_here
```

Then start the app:

```powershell
python Day20_exercise.py
```

Open http://localhost:5000.

The optional `ANTHROPIC_MODEL` variable overrides the default model. `LOG_LEVEL` may be used to control application log verbosity.

**Security:** Never commit `.env`, API keys, or customer-sensitive information. The repository `.gitignore` should keep local secret files out of version control.

## Test

Run the automated suite:

```powershell
python -m unittest -v test_app.py
```

The suite covers homepage rendering, complaint validation, 4,000-character and HTTP body limits, malformed requests, missing API configuration, provider response parsing, retries, and permanent provider failures. Provider calls are mocked, so tests do not require an API key or contact Anthropic.

### Browser smoke checks

The current release was also checked with mocked `/api/reply` responses for:

- Required-field and character-limit handling
- Successful reply generation
- Service and network errors
- Malformed API responses
- Clipboard success and fallback behavior

## Offline behavior

Once Python dependencies are installed, the Flask page can load without internet access. Reply generation requires a live Anthropic API connection and a valid key. The deployed service has the same requirement. Google Fonts are optional; the interface falls back to local browser fonts when unavailable.

## Using the app

1. Open the app.
2. Paste the customer's complaint.
3. Select **Generate reply**.
4. Review and personalize the draft.
5. Select **Copy reply** and paste it into the business support channel.

The app does not automatically send messages or copy drafts. It provides a draft for staff review.

## Deploy to Render

1. Push the repository to GitHub.
2. In Render, create a Blueprint service from `render.yaml`.
3. Set `ANTHROPIC_API_KEY` in the Render environment settings.
4. Optionally set `ANTHROPIC_MODEL` or `LOG_LEVEL`.
5. Deploy and open the generated public URL.

The Blueprint uses Gunicorn and the `/` homepage for the health check. Render may take extra time to start the free-tier service after inactivity.

## Handover and maintenance

- Keep the Anthropic key in the hosting provider's secret environment settings.
- Rotate the key immediately if it is exposed.
- Review and personalize every generated response before sending it.
- Monitor Render logs and Anthropic usage/billing.
- Restrict use to approved business and customer-support purposes.
- Do not add payment-card, password, or identity-document data to the complaint field.

## Branded version scope and price

A branded version for one business can include the business logo and colors, tailored response tone, deployment, staff handover, and a one-page usage guide.

Reference price: **KES 25,000 one-time**, with ongoing Anthropic usage billed separately at provider cost. A recurring support arrangement may be agreed separately.
