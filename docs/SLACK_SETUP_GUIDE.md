# How to Get Your Slack Tokens 🔑

The **Client ID** and **Secret** you provided are for *configuring* the app, but to **connect** the agent, we need **Access Tokens**.

### 1. Get the Bot Token
1.  Go to the [Slack API Dashboard](https://api.slack.com/apps).
2.  Click on your app **"Who Visions"**.
3.  In the left sidebar, click **"OAuth & Permissions"**.
4.  Scroll down to **"Scopes"** -> **"Bot Token Scopes"**.
    -   Add: `chat:write`
    -   Add: `app_mentions:read`
    -   Add: `channels:history`
5.  Scroll BACK UP to the top of the page.
6.  Click the likely green button: **"Install to Workspace"**.
7.  Allow the permissions.
8.  You will see **"Bot User OAuth Token"**.
9.  👉 **Copy this string.**

### 2. Get the App-Level Token
1.  In the left sidebar, click **"Basic Information"**.
2.  Scroll down to the section **"App-Level Tokens"**.
3.  Click **"Generate Token and Scopes"**.
    -   Name: `Socket Mode`
    -   Click **"Add Scope"** and select `connections:write`.
4.  Click **"Generate"**.
5.  You will see the generated token.
6.  👉 **Copy this string.**

---

### Action Required
Please paste both tokens in the chat:
```
BOT_TOKEN
APP_LEVEL_TOKEN
```
