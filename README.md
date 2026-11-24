# ReplyWell

**Live URL:** https://replywell.onrender.com

ReplyWell helps small Nairobi businesses respond to customer complaints with care. Paste a complaint from a shop, courier, Airbnb, or restaurant customer and select **Generate reply** to get a professional draft that acknowledges the issue and suggests a clear next step. It avoids blame and unsupported promises. Review and personalize the draft before sending.

Complaint text is sent to Anthropic for drafting; avoid entering payment details or other sensitive information.

# Project Brief

**Project:** ReplyWell — AI Customer Reply Assistant  
**Client:** Small businesses in Nairobi, Kenya  
**Problem:** Staff struggle to write quick, calm, and professional responses to customer complaints.  
**Solution:** A Python Flask app that lets users paste a complaint and receive an AI-generated reply draft for review and sending.  
**Deliverables:** Working web app, Anthropic API setup instructions, one-page user guide, and handover guidance  
**Timeline:** 5 days: Day 1 (setup), Day 2 (UI), Day 3 (AI integration), Day 4 (testing), Day 5 (deployment)  
**Price:** KES 25,000 one-time build + KES 2,000/month support

## What was built

ReplyWell is a Flask app that validates complaint submissions and uses Anthropic to generate a concise, professional reply draft. It logs request and provider outcomes without logging complaint text, and retries transient provider failures up to three times.

## Run locally

1. Install dependencies with `python -m pip install -r requirements.txt`.
2. Set `ANTHROPIC_API_KEY` in your local `.env` file. Never commit the key.
3. Run `python Day20_exercise.py` and open `http://localhost:5000`.

Run the test suite with `python -m unittest -v test_app.py`. Tests use mocked provider responses and do not call Anthropic.

## Deploy to Render

This project includes a `render.yaml` Blueprint. Connect the Git repository to Render, create the Blueprint service, and provide `ANTHROPIC_API_KEY` in the Render dashboard. Render will display the public service URL after deployment.

## Branded version pricing

I would charge **KES 25,000** as a one-time setup for a branded version for one business, including its logo and colors, tailored response tone, deployment, and handover. Ongoing AI usage would be billed separately at cost.
