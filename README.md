Python Gmail Sender Setup Guide (Using OAuth 2.0)

This guide explains how to properly authenticate your Python script using the secure Google Gmail API and OAuth 2.0 workflow.

1. Prerequisites: Install Libraries

You must install the Google API Python client and the necessary authentication libraries.

pip install google-auth google-auth-oauthlib google-api-python-client


2. Google Cloud Setup & Credentials

This process involves setting up a project in Google Cloud, enabling the Gmail API, and generating the credentials.json file.

Step 2.1: Create a Google Cloud Project

Go to the Google Cloud Console.

Click the project selector dropdown and click New Project.

Give it a name (e.g., Gmail Sender) and click Create.

Step 2.2: Enable the Gmail API

In the Google Cloud Console, navigate to APIs & Services > Library.

Search for Gmail API and click on it.

Click the Enable button.

Step 2.3: Configure the OAuth Consent Screen (I found that I didn't need this)

In the Google Cloud Console, navigate to APIs & Services > OAuth consent screen.

Select External and click CREATE.

Fill in the required fields (App name, User support email, Developer contact information).

On the Scopes step, click ADD OR REMOVE SCOPES. Search for and select the scope:

.../auth/gmail.send (Sends mail)

Save and continue through the remaining steps. For testing purposes, you can leave it in Testing status.

Step 2.4: Download credentials.json

In the Google Cloud Console, navigate to APIs & Services > Credentials.

Click + CREATE CREDENTIALS and select OAuth client ID.

For Application type, choose Desktop app (since you are running it from your computer).

Give it a name (e.g., Python Desktop Client) and click CREATE.

A pop-up will show your Client ID and Client Secret. Click DOWNLOAD JSON.

Rename the downloaded file to credentials.json and place it in the same directory as your Python script (send_email.py).

3. Running and Authorizing the Script

Step 3.1: Initial Run & Authorization

Ensure you have installed the prerequisites and placed credentials.json in the script directory.

Run the script:

python send_email.py

NOTE: This must be run on a machine with a browser. If you want this to eventually be headless, please run initially on a browser, then copy token.json to the headless machine.

Browser Window: On the first run, the script will automatically open a browser window asking you to log in to your Google Account and grant permission (the gmail.send scope) to your application.

Grant Access: Log in and click Allow/Continue. The browser will redirect, and the script will capture the authorization token.

Token File: The script will automatically create a file named token.json and store your refresh token there. This file allows the script to remain authenticated for future runs without prompting you again (until the token is revoked or expires).

Step 3.2: Subsequent Runs

For all future runs, the script will use the stored token.json file to authenticate, and the process will be automatic and secure.

Important: You must update the SENDER_EMAIL variable inside the Python script to match the email address of the Google Account you use for authorization.