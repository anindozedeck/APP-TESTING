# ReplyWell One-Page Retrospective

**Date:** 28 November 2026

## What was delivered

ReplyWell is a complete Flask web application for generating calm, review-before-sending customer-support reply drafts. The handoff includes the Anthropic integration, responsive HTML interface, provider retry and validation logic, automated tests, deployment configuration, staff walkthrough, delivery message, invoice template, and feedback log.

## What worked well

- The HTML page layout was clear and usable.
- Validation covered missing complaints, malformed payloads, character limits, HTTP size limits, and provider failures.
- The test suite verified 17 behavior and error-handling scenarios.
- The interface showed loading, success, and error states without exposing complaint text in application logs.
- Local smoke testing returned HTTP 200 and rendered the expected page title.

## Feedback received

The reviewer rated the project **Good** and positively identified the HTML page layout. The reviewer requested automatic copying of feedback, but the intended destination was not specified. For ReplyWell drafts, copying remains an explicit **Copy reply** action so staff can review text before it reaches a support channel or clipboard.

## Challenges and decisions

The provider is external, so network and API failures needed controlled retries and clear 503 responses. Complaint text was kept out of logs, and response output was checked before it reached the browser. Clipboard behavior was left user-initiated because automatic copying can be blocked or silently copy sensitive information.

## What could improve next

- Clarify whether the remaining request is automatic reply copying or copying feedback from another workflow.
- Add browser automation for the loading, success, error, and clipboard states.
- Add environment-variable checks to a deployment startup diagnostic.
- Gather feedback from several real support staff after a short live trial.
- Review provider usage and cost after actual production traffic.
