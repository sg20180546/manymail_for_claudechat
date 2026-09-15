# Privacy Policy — manymail_for_claudechat

**Last updated: 2026-09-15**

`manymail_for_claudechat` ("the app") is an open-source [Model Context Protocol](https://modelcontextprotocol.io)
server that lets an AI assistant running on your own computer read and write your Gmail. It is run by
the person who installs it, on their own machine, with their own Google Cloud OAuth client.

There is no hosted service behind this app. The author does not operate any server that receives your
data and cannot see your mail.

## What the app accesses

The app requests a single OAuth scope:

| Scope | What it allows |
|---|---|
| `https://www.googleapis.com/auth/gmail.modify` | Read, search, label, archive, draft and send mail on your behalf |

This scope does **not** allow permanently deleting messages or changing account settings.

## What is stored, and where

Everything is stored on your own computer, in the directory where you installed the app:

| Data | Location | Notes |
|---|---|---|
| OAuth access and refresh tokens | `tokens/<account>.json` | Written with `0600` permissions |
| OAuth client id and secret | `credentials.json`, `credentials-<account>.json` | Downloaded by you from Google Cloud Console |
| Attachments you download | `~/MailOutbox/downloads/` | Only when you ask the assistant to download one |

Nothing is written to any remote location by the app. Message contents are not cached or logged to
disk by the app.

## Where your mail actually goes

**Please read this part carefully.** The app hands message contents to whichever AI assistant you
connect it to — for example Claude Desktop, Claude Code, or the ChatGPT desktop app. Those clients
send the text of your conversation, including any mail content the assistant retrieved, to their own
provider's servers for processing.

That transfer is governed by the privacy policy of the client you chose, not by this document:

- Anthropic — <https://www.anthropic.com/legal/privacy>
- OpenAI — <https://openai.com/policies/privacy-policy>

If you are not comfortable with your mail being processed by those providers, do not connect this app
to them.

## What the author receives

Nothing. The app sends no telemetry, analytics, crash reports, or usage data to the author or to any
third party. The author has no access to your Google account, your tokens, or your mail.

## Sharing

The app does not sell, rent, or share your data with anyone. The only network destinations it contacts
are Google's own API endpoints (`googleapis.com`, `oauth2.googleapis.com`) to carry out the actions you
ask for.

## Retention and deletion

Tokens and downloaded files stay on your machine until you delete them.

To revoke the app's access entirely:

1. Delete the token file(s): `rm tokens/<account>.json`
2. Remove the grant at <https://myaccount.google.com/connections>

Revoking at step 2 immediately invalidates the stored tokens.

## Limited Use disclosure

This app's use of information received from Google APIs adheres to the
[Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy),
including the Limited Use requirements.

## Changes

Changes to this policy are published in this file in the project's public repository, with the date at
the top updated.

## Contact

Open an issue at <https://github.com/sg20180546/manymail_for_claudechat/issues>.
