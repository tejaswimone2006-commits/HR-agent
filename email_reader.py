import imaplib
import email
import os

EMAIL = "tejaswimone2006@gmail.com"
PASSWORD = "tzxl jdew yhbx fzgr"

def fetch_resumes():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    result, data = mail.search(None, '(UNSEEN)')
    email_ids = data[0].split()

    for e_id in email_ids:
        result, msg_data = mail.fetch(e_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()
                if filename.endswith((".pdf", ".docx")):
                    filepath = os.path.join("data", filename)
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))

    mail.logout()