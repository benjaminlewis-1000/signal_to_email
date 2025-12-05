import os
import sys
import base64
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Import necessary Google API and auth libraries
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("--- DEPENDENCY ERROR ---")
    print("You are missing required Python libraries. Please run:")
    print("pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)


# Define the required scope for sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
# Files used for storing credentials
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

class GmailSender:
    """
    A class to handle secure authentication to the Gmail API via OAuth 2.0
    and manage the creation and sending of emails with attachments.
    """
    def __init__(self, sender_email: str = None):
        """
        Initializes the sender object. Authentication is delayed if sender_email is None.

        Args:
            sender_email (str, optional): The email address of the authenticated sender. 
                                          If provided, authentication happens immediately.
        """
        self.sender_email = sender_email
        self.subject = ""
        self.body = ""
        self.recipients = []
        self.attachment_paths = []
        self.service = None
        
        # Authenticate immediately if the sender email is known
        if self.sender_email:
            self.service = self._authenticate_gmail()
        
    def _authenticate_gmail(self):
        """
        Handles the OAuth 2.0 flow, returning the authorized Gmail API service.
        This method must only be called once self.sender_email is set.
        """
        if not self.sender_email:
            print("Authentication Error: Cannot authenticate. Sender email is not set.")
            return None
            
        creds = None
        
        # Load credentials from token.json if it exists (for subsequent runs)
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    print(f"Error: Missing {CREDENTIALS_FILE}. Please follow the README instructions.")
                    return None

                print("Starting OAuth flow. A browser window will open shortly...")
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"Error during OAuth flow: {e}")
                    return None
                
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
                print(f"Authentication successful. Token saved to {TOKEN_FILE}.")
        
        try:
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            print(f"Error building Gmail service: {e}")
            return None

    def set_message(self, subject: str, body: str):
        """Sets the subject and body content of the email."""
        self.subject = subject
        self.body = body

    def add_attachment(self, file_path: str):
        """Adds a single file path to the list of attachments."""
        if os.path.exists(file_path):
            self.attachment_paths.append(file_path)
            print(f"Attachment path added: {file_path}")
        else:
            print(f"Warning: File not found at path: {file_path}. Not adding.")

    def load_recipients_from_json(self, json_file_path: str, recipients_key: str = "recipients", sender_key: str = "sender_email"):
        """
        Reads a configuration file to set the sender email and the list of recipients.
        The JSON must contain a list of strings under the 'recipients_key' and 
        a string under the 'sender_key'.
        
        Returns:
            bool: True if loading was successful, False otherwise.
        """
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
                
                # 1. Load Sender Email
                sender_email = data.get(sender_key)
                if not isinstance(sender_email, str) or not sender_email:
                    print(f"Error: JSON file must contain a valid string under the key '{sender_key}'.")
                    return False
                
                self.sender_email = sender_email
                print(f"Sender email set to: {self.sender_email}")
                
                # 2. Load Recipients
                emails = data.get(recipients_key, [])
                if isinstance(emails, list) and all(isinstance(e, str) for e in emails):
                    self.recipients = emails
                    print(f"Successfully loaded {len(self.recipients)} recipients from {json_file_path}.")
                else:
                    print(f"Error: JSON file must contain a list of strings under the key '{recipients_key}'.")
                    return False
                
                # 3. Authenticate if not already done (after sender_email is set)
                if not self.service:
                    self.service = self._authenticate_gmail()
                    
                return self.service is not None
                
        except FileNotFoundError:
            print(f"Error: Configuration JSON file not found at path: {json_file_path}")
            return False
        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON from file: {json_file_path}")
            return False

    def _create_raw_message(self):
        """
        Creates a full MIME message with text and attachments, ready for API transmission.
        
        NOTE: The email body is now wrapped in HTML with a larger font size.
        
        Returns:
            The base64url encoded raw message dict, or None on failure.
        """
        if not self.recipients:
            print("Error: No recipients defined. Cannot create message.")
            return None

        message = MIMEMultipart()
        message['to'] = ", ".join(self.recipients)
        message['from'] = self.sender_email
        message['subject'] = self.subject
        
        # --- HTML Body Creation ---
        # 1. Wrap the plain text body in a simple HTML structure
        # 2. Use <pre> tag to preserve formatting (newlines, spaces) from the original string
        # 3. Apply CSS style to increase the font size (e.g., 14pt)
        html_body = f"""
        <html>
          <body>
            <div style="font-size: 14pt; font-family: Arial, sans-serif; line-height: 1.5;">
              <pre style="white-space: pre-wrap; margin: 0; padding: 0;">{self.body}</pre>
            </div>
          </body>
        </html>
        """
        
        # Attach the body text as HTML
        message.attach(MIMEText(html_body, 'html', 'utf-8'))

        # Handle attachments
        for file_path in self.attachment_paths:
            try:
                with open(file_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)

                import os.path
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {os.path.basename(file_path)}",
                )
                message.attach(part)
            except Exception as e:
                print(f"Error processing attachment {file_path}: {e}. Skipping.")
        
        # Encode the entire message into a base64url string
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw_message}


    def send_email(self):
        """
        Constructs the message and sends it via the authorized Gmail API service.
        """
        if not self.service:
            print("Cannot send email: Gmail service is not initialized (check authentication).")
            return
        
        if not self.recipients:
            print("Cannot send email: No recipients have been loaded.")
            return

        try:
            # Create the message structure for the API
            message = self._create_raw_message()

            if message:
                # Send the message using the Gmail API
                sent_message = self.service.users().messages().send(userId='me', body=message).execute()
                
                print("\n--- SEND SUCCESS ---")
                print(f"Email successfully sent from {self.sender_email} to: {', '.join(self.recipients)}")
                print(f"Gmail Message ID: {sent_message.get('id', 'N/A')}")
            else:
                print("Email construction failed. Check logs for details.")

        except HttpError as error:
            print(f"\n--- Gmail API Error Occurred ---")
            print(f'Details: {error}')
        except Exception as e:
            print(f"\n--- An unexpected error occurred ---")
            print(f"Error: {e}")


# --- Main Execution Block ---
if __name__ == "__main__":
    
    # 1. Initialize the Sender object without a sender email (it will be loaded from JSON)
    sender = GmailSender()

    # 2. Load sender and recipients from the JSON file and trigger authentication
    recipient_file = "recipients.json"
    if not sender.load_recipients_from_json(recipient_file):
        print("Failed to load configuration and authenticate. Exiting.")
        sys.exit(1)
        
    # Check if authentication was successful after loading config
    if sender.service:
        
        # 3. Set the message content
        EMAIL_SUBJECT = "Signal Dec 4 2025"
        EMAIL_BODY = (
            "Hello, you're getting a signal message without an attachment!"
        )
        sender.set_message(EMAIL_SUBJECT, EMAIL_BODY)
        
        
        # 5. Send the email
        sender.send_email()
        
        # 4. Add attachments one by one
        sender.add_attachment("bridge.jpeg")
        sender.send_email()