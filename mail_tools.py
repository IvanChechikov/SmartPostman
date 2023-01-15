import base64
import imaplib
import re
import smtplib
import email
import email.header
from email.header import decode_header
from email.headerregistry import Address
from email.message import EmailMessage

import requests

login_info_url = "https://login.yandex.ru/info?oauth_token={}"
email_address_list = []


def get_sender_email_data(access_token: str) -> list:
    response = requests.get(login_info_url.format(access_token))
    user_data = response.json()
    sender_name = user_data["display_name"]
    sender_email = user_data["default_email"]
    return [sender_name, sender_email]


def send_email(access_token: str, sender_email_name: str, sender_email: str, recipient_email_name: str,
               recipient_email: str, subject: str, message: str) -> bool:
    try:
        just_a_str = f"user={sender_email}\x01auth=Bearer {access_token}\x01\x01"
        xoauth2_token = base64.b64encode(bytes(just_a_str, 'utf-8')).decode('utf-8')

        sender_email_login = get_email_data_list(sender_email)[0]
        sender_email_domain = get_email_data_list(sender_email)[1]
        recipient_email_login = get_email_data_list(recipient_email)[0]
        recipient_email_domain = get_email_data_list(recipient_email)[1]

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = Address(sender_email_name, sender_email_login, sender_email_domain)
        msg['To'] = Address(recipient_email_name, recipient_email_login, recipient_email_domain)
        msg.set_content(message)

        smtp = smtplib.SMTP_SSL(host='smtp.yandex.ru', port=465)
        smtp.connect(host='smtp.yandex.ru', port=465)
        smtp.docmd("auth", f"XOAUTH2 {xoauth2_token}")
        smtp.sendmail(sender_email, recipient_email, msg.as_string())
        smtp.quit()
    except IndexError:
        return False
    
    return True


def get_email_data_list(email_data_str: str) -> list:
    email_data_list = email_data_str.split("@")
    return email_data_list


def get_email_address_list(access_token: str, sender_email: str) -> list:
    try:
        xoauth2_token = f"user={sender_email}\x01auth=Bearer {access_token}\x01\x01"
    
        imap = imaplib.IMAP4_SSL(host='imap.yandex.com')
        imap.debug = 4
        imap.authenticate("XOAUTH2", lambda x: xoauth2_token)
        status, messages = imap.select("INBOX")
        messages = int(messages[0])
        messages_count = 0
        if messages >= 30:
            messages_count = 30
        elif messages < 30:
            messages_count = messages
        while messages_count:
            messages_count -= 1
            res, msg = imap.fetch(str(messages - messages_count), "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])

                    sender_data = decode_header(msg.get("From"))

                    if len(sender_data) == 2:
                        sender_name, encoding = sender_data[0]
                        sender_email, type_email = sender_data[1]
                        if isinstance(sender_name, bytes) and isinstance(sender_email, bytes):
                            sender_name = sender_name.decode(encoding)
                            sender_name = ''.join(sender_name.split()).lower()
                            sender_email = sender_email.decode(encoding).replace("<", "") \
                                .replace(">", "").replace(" ", "")
                            sender_email = sender_email.lower()
                            email_address_list.append(sender_name + ":" + sender_email)
            
        imap.close()
        imap.logout()
        
    except Exception:
        return []
    
    return email_address_list


def get_recipient_email_text(text: str) -> list:
    try:
        email_text = ''.join(text.split()).lower()
        email_text = email_text.split("получатель")[1]
        for email_recipient in email_address_list:
            if email_text in email_recipient:
                recipient_name = email_recipient.split(":")[0]
                recipient_email = email_recipient.split(":")[1]
                return [recipient_name, recipient_email]

    except Exception:
        return []
    return []


def get_email_obj_text(email_obj_text: str, email_obj_type: str) -> str:
    email_obj_text_list = email_obj_text.split(email_obj_type + " ") \
        if len(email_obj_text.split(email_obj_type + " ")) > 1 \
        else email_obj_text.split(email_obj_type.title() + " ")
    email_obj_text = email_obj_text_list[1]
    email_obj_text = email_obj_text.replace(" точка с запятой", ";")
    email_obj_text = email_obj_text.replace(" точка", ".")
    email_obj_text = email_obj_text.replace(" знак восклицания", "!")
    email_obj_text = email_obj_text.replace(" восклицательный знак", "!")
    email_obj_text = email_obj_text.replace(" знак вопроса", "?")
    email_obj_text = email_obj_text.replace(" вопросительный знак", "?")
    email_obj_text = email_obj_text.replace("тире", "-")
    email_obj_text = email_obj_text.replace(" двоеточие", ":")
    email_obj_text = email_obj_text.replace(" запятая", ",")

    email_obj_text_list = re.findall(r"[\sА-Яа-я-,;:_-]*!?.", email_obj_text)
    text_list = []
    for phrase in email_obj_text_list:
        phrase = phrase.strip()
        phrase = phrase.capitalize()
        text_list.append(phrase)
    email_obj_text = " ".join(text_list)
    return email_obj_text
