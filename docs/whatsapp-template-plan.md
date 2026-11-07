# Plan: WhatsApp template messages in Switch

Goal: let a Switch agent message someone on WhatsApp when their 24-hour window is closed, so Parent Line can alert the trusted person on WhatsApp, not only by SMS.

This is a change to the Switch WhatsApp adapter, not to Parent Line. It goes upstream as its own PR, on a new branch stacked on `feat/whatsapp-adapter` (sandbox-quantum/switch#1166, still open), so #1166's review doesn't grow.

## What exists today

- `WhatsAppAdapter._send` turns Meta error `131047` (window closed) into `BridgeOperationError(WINDOW_CLOSED)`. Nothing is retried.
- A room can already be bound to a WhatsApp number: the adapter keeps the base `require_bindable_channel`, which refuses nothing, and `_address` sends to a digits-only chat id as `to`. So "message someone first" already reaches Meta; Meta refuses it for the window.
- There is no allowed-numbers list on WhatsApp (SMS has one). Free-form sends can't reach a stranger anyway, because of the window. Templates can, and each costs money.

## The change

### 1. Connection config (`WhatsAppConnectionConfig`)

Three new fields, all empty by default. They are set together or not at all; a validator refuses a partial set.

| Field | Meaning |
|---|---|
| Template name | An approved template, category Utility, whose body has exactly one variable, `{{1}}` |
| Template language | Its language code, such as `en` or `hi` |
| Numbers that may get a template | E.164 numbers. A template goes only to these. Stops a bound room from messaging anyone, at Meta's price |

Probably a fourth: **WhatsApp Business Account ID**, so saving can check the template (below). Confirm whether the phone number's Graph object can give it instead, and skip the field if so.

### 2. Sending (`_send_text`)

Try free-form first, as now. Only when Meta answers `131047`:

- No template configured → raise `WINDOW_CLOSED`, as now. Its text gains one sentence saying a template can be set on the connection.
- Recipient not in the template list → raise, naming the last four digits and the field to add them to.
- Otherwise send one template message instead of the chunks: `{"type": "template", "template": {"name", "language": {"code"}, "components": [{"type": "body", "parameters": [{"type": "text", "text": ...}]}]}}`. The parameter is the whole message, with the agent label, collapsed onto one line and cut with `…` to fit Meta's parameter rules (no newlines or tabs, no runs of spaces, a length limit). Check the exact limits against Meta's docs when implementing.

Trying free-form first means no window tracking: a refused send isn't billed, and Switch keeps no state a second instance would need.

Only text messages fall back. Attachments, reactions and request cards outside the window still fail as they do now.

### 3. Template refusals fail loudly

Meta's template errors (template missing, paused, disabled, wrong parameter count, parameter format) become `BridgeOperationError` with Meta's own message and the template name. No retry, no silent drop.

### 4. Check on save (`verify_credentials`)

When a template is set, read it back from Meta and refuse to save unless it exists in that language, is approved, and has exactly one body variable. A wrong template name must show up when the connection is saved, not when the first alert goes out.

### 5. Cost bound (decide)

Templates cost money per message. SMS limits texts per number per hour (`sms/budget.py`). Options:

- reuse the same pattern for templates per number per hour (small default, say 5), or
- rely on the template list being short and leave it out.

Recommendation: add the cap. An agent stuck in a loop outside the window would otherwise send a paid template on every turn.

## Tests (`test_whatsapp_adapter.py`, beside the existing `131047` tests)

- `131047` with a template configured sends exactly one template payload, carrying the message on one line
- `131047` with no template still raises `WINDOW_CLOSED`
- a recipient outside the template list is refused before any template is sent
- a long, multi-line message is collapsed and cut to fit
- each Meta template error surfaces with its message
- config: a partial template set is refused; a bad E.164 number is refused
- save: a template that is missing, unapproved, or has the wrong variable count is refused
- the cap, if added: past it, nothing is sent and the refusal says so

## Docs

`docs/messaging-platforms/whatsapp.md`: replace "Switch doesn't send templates" with how to create the template in Meta (Utility, one variable, approval time), the new fields, and the cost.

## For Parent Line

Create the template in Meta Business Manager before the demo, in English and Hindi (one template per language). Meta may reject a body that is almost all variable, so give it fixed text around `{{1}}`, for example:

> This is an alert from Parent Line about your family member. {{1}} Reply here to talk to the guardian.

The trusted person's reply opens the 24-hour window, and the guardian's next messages go out free-form.

## Open questions

- Meta's exact parameter limits and template error codes: check against current Graph docs.
- Whether the WhatsApp Business Account ID can be read from the phone number instead of being a new field.
- One language per connection, or a template per language? One is enough for the hackathon.
