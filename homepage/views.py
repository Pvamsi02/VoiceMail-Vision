from django.shortcuts import render, redirect
from . import forms
from .models import Details
from .models import Compose
import imaplib, email
from gtts import gTTS
import os
from playsound import playsound
from django.http import HttpResponse, HttpResponseRedirect
import speech_recognition as sr
import smtplib
from django.http import JsonResponse
import re
from email.message import EmailMessage
import ssl
import logging
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from email.header import decode_header
from email import message_from_bytes
import imaplib
from gtts import gTTS
import os
from tempfile import NamedTemporaryFile
from decouple import config

email_sender = config("EMAIL_ADDRESS")
email_password = config("EMAIL_PASSWORD")
file = "good"
i = "0"
passwrd = ""
addr = ""
item = ""
subject = ""
body = ""
logger = logging.getLogger("__name__")
s = smtplib.SMTP("smtp.gmail.com", 587)
s.starttls()
imap_url = "imap.gmail.com"
conn = imaplib.IMAP4_SSL(imap_url)
smtp_session = None
smtp_session1 = None

logger = logging.getLogger("__name__")


def login_imap(email_address, password):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_address, password)
        return mail
    except Exception as e:
        logger.error(f"Failed to login: {str(e)}")
        raise e


def texttospeech(text, filename):
    filename = filename + ".mp3"
    flag = True
    while flag:
        try:
            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(filename)
            flag = False
        except:
            print("Trying again")
    playsound(filename)
    os.remove(filename)
    return


def speechtotext(duration):
    global i, addr, passwrd
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=1)
            playsound("speak.mp3")
            audio = r.listen(source, phrase_time_limit=duration)
            response = r.recognize_google(audio)
            response = response.lower()
            print(response)
    except:
        response = "N"
    return response


def convert_special_char(text):
    temp = text
    special_chars = [
        "attherate",
        "dot",
        "underscore",
        "dollar",
        "hash",
        "star",
        "plus",
        "minus",
        "space",
        "dash",
    ]
    for character in special_chars:
        while True:
            pos = temp.find(character)
            if pos == -1:
                break
            else:
                if character == "attherate":
                    temp = temp.replace("attherate", "@")
                elif character == "dot":
                    temp = temp.replace("dot", ".")
                elif character == "underscore":
                    temp = temp.replace("underscore", "_")
                elif character == "dollar":
                    temp = temp.replace("dollar", "$")
                elif character == "hash":
                    temp = temp.replace("hash", "#")
                elif character == "star":
                    temp = temp.replace("star", "*")
                elif character == "plus":
                    temp = temp.replace("plus", "+")
                elif character == "minus":
                    temp = temp.replace("minus", "-")
                elif character == "space":
                    temp = temp.replace("space", "")
                elif character == "dash":
                    temp = temp.replace("dash", "-")
    return temp


def introduction_view(request):
    global i
    text1 = "Welcome to our Voice Based Email. Login with your email account in order to continue. "
    texttospeech(text1, file)
    i = i + str(1)
    return render(request, "homepage/introduction.html")


def login_view(request):
    email_address = config("EMAIL_ADDRESS")
    password = config("EMAIL_PASSWORD")

    global smtp_session
    email_sender = config("EMAIL_ADDRESS")
    email_password = config("EMAIL_PASSWORD")
    context = ssl.create_default_context()
    conn = login_imap(email_sender, email_password)
    if not email_address or not password:
        return redirect("homepage:login")

    try:
        if smtp_session is None:
            smtp_session = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context)
            smtp_session.login(email_sender, email_password)
            texttospeech("Login successful! Redirecting to the main menu.", file + i)
            return render(request, "homepage/options.html")
        conn = login_imap(email_address, password)
        request.session["imap_conn"] = conn
        return redirect("homepage:inbox")

    except smtplib.SMTPAuthenticationError:
        return JsonResponse(
            {
                "result": "failure",
                "message": "Authentication failed, please check your credentials",
            }
        )
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        return HttpResponse(f"Failed to log in: {str(e)}")


def logout_view(request):
    return HttpResponseRedirect("/")


def options_view(request):
    global i, addr, passwrd
    if request.method == "POST":
        flag = True
        texttospeech(
            "You are logged into your account. What would you like to do ?", file + i
        )
        i = i + str(1)
        while flag:
            texttospeech(
                "To compose say compose To open Inbox folder say Inbox. To open Sent folder say delivered. To open Trash folder say Trash. To Logout say Logout. Do you want me to repeat? if no say skip.",
                file + i,
            )

            i = i + str(1)
            say = speechtotext(3)
            texttospeech(say, file + i)
            if say == "do not" or say == "skip":
                flag = False
        texttospeech("Enter your desired action", file + i)
        i = i + str(1)
        act = speechtotext(5)
        texttospeech(act, file + i)
        act = act.lower()
        if act == "compose":
            return JsonResponse({"result": "compose"})
        elif act == "inbox":
            return JsonResponse({"result": "inbox"})
        elif act == "sent" or act == "delivered":
            return JsonResponse({"result": "sent"})
        elif act == "trash bin" or act == "trash" or act == "trashbin":
            return JsonResponse({"result": "trash"})
        elif act == "log out" or act == "logout":
            addr = ""
            passwrd = ""
            texttospeech(
                "You have been logged out of your account and now will be redirected back to the login page.",
                file + i,
            )
            i = i + str(1)
            return JsonResponse({"result": "logout"})
        else:
            texttospeech("Invalid action. Please try again.", file + i)
            i = i + str(1)
            return JsonResponse({"result": "failure"})
    elif request.method == "GET":
        return render(request, "homepage/options.html")


def compose_view(request):
    global i, addr, passwrd, s, item, subject, body
    if request.method == "POST":
        text1 = "You have reached the page where you can compose and send an email. "
        texttospeech(text1, file + i)
        i = i + str(1)
        flag = True
        fromaddr = addr
        toaddr = list()

        while flag:
            texttospeech("Enter receiver's email address:", file + i)
            i = i + str(1)
            to = ""
            to = speechtotext(15)
            if to != "":
                texttospeech(
                    "You meant "
                    + to
                    + ". Say proceed to confirm or no to enter again.",
                    file + i,
                )
                i = i + str(1)
                say = speechtotext(5)
                if say in ["yes", "Yes", "yeah", "proceed"]:
                    toaddr.append(to)
                    flag = False
            else:
                texttospeech("Could not understand what you meant.", file + i)
                i = i + str(1)

        newtoaddr = list()
        for item in toaddr:
            item = item.strip()
            item = item.replace(" ", "")
            item = item.lower()
            item = convert_special_char(item)
            newtoaddr.append(item)
            print(item)
        msg = EmailMessage()
        fromaddr = email_sender
        msg["From"] = fromaddr
        msg["To"] = ",".join(newtoaddr)
        flag = True
        while flag:
            texttospeech("enter subject", file + i)
            i = i + str(1)
            subject = speechtotext(10)
            if subject == "N":
                texttospeech("could not understand what you meant", file + i)
                i = i + str(1)
            else:
                flag = False
        msg["Subject"] = subject
        flag = True
        body = "body of mail"
        while flag:
            texttospeech("enter body of the mail", file + i)
            i = i + str(1)
            body = speechtotext(20)
            if body == "N":
                texttospeech("could not understand what you meant", file + i)
                i = i + str(1)
            else:
                flag = False
        msg.set_content(body)
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.send_message(msg)
                texttospeech(
                    "Your email has been sent successfully. You will now be redirected to the menu page.",
                    file + i,
                )
                return JsonResponse({"result": "success"})
        except Exception as e:
            print(e)
            texttospeech(
                "Sorry, your email failed to send. please try again. You will now be redirected to the the compose page again.",
                file + i,
            )
            return JsonResponse({"result": "failure"})
    compose = Compose()
    compose.recipient = item
    compose.subject = subject
    compose.body = body

    return render(request, "homepage/compose.html", {"compose": compose})


def get_body(msg):
    if msg.is_multipart():
        return get_body(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)


def login_imap(email_address, password):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_address, password)
        return mail
    except Exception as e:
        logger.error(f"Failed to login: {str(e)}")
        raise e


def decode_body(body_bytes):
    """Try different decodings to handle various encodings in email body"""
    encodings = ["utf-8", "latin-1", "iso-8859-1"]
    for encoding in encodings:
        try:
            return body_bytes.decode(encoding)
        except (UnicodeDecodeError, TypeError):
            continue
    return body_bytes.decode("utf-8", errors="ignore")


def inbox_view(request):
    email_address = config("EMAIL_ADDRESS")
    password = config("EMAIL_PASSWORD")

    if not email_address or not password:
        return redirect("homepage:login")

    try:
        conn = login_imap(email_address, password)
        conn.select("inbox")
        result_unread, data_unread = conn.search(None, "UNSEEN")
        unread_list = data_unread[0].split()
        no_unread = len(unread_list)

        if no_unread == 0:
            return render(
                request, "homepage/inbox.html", {"message": "No unread emails."}
            )

        unread_emails = []
        for email_id in unread_list:
            result, email_data = conn.fetch(email_id, "(RFC822)")
            raw_email = email_data[0][1]
            msg = message_from_bytes(raw_email)
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")
            from_ = decode_header(msg.get("From"))[0]
            if isinstance(from_[0], bytes):
                from_ = from_[0].decode(from_[1] if from_[1] else "utf-8")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True)
                        break
            else:
                body = msg.get_payload(decode=True)
            body = decode_body(body)
            unread_emails.append({"subject": subject, "from": from_, "body": body})
            tts = gTTS(
                text=f"Subject: {subject}. From: {from_}. Body: {body[:300]}...",
                lang="en",
            )
            with NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                audio_path = fp.name
                tts.save(audio_path)
                fp.close()
            unread_emails[-1]["audio_path"] = audio_path
        return render(
            request,
            "homepage/inbox.html",
            {
                "unread_emails": unread_emails,
                "message": f"You have {no_unread} unread emails. Content is being read aloud.",
            },
        )

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return HttpResponse(f"Failed to fetch emails: {str(e)}")

    finally:
        if conn:
            conn.logout()


def sent_view(request):
    email_address = config("EMAIL_ADDRESS")
    password = config("EMAIL_PASSWORD")

    if not email_address or not password:
        return redirect("homepage:login")

    try:
        conn = login_imap(email_address, password)
        conn.select('"[Gmail]/Sent Mail"')
        result, data = conn.search(None, "ALL")
        email_ids = data[0].split()

        sent_emails = []
        for email_id in email_ids:
            result, email_data = conn.fetch(email_id, "(RFC822)")
            raw_email = email_data[0][1]
            msg = message_from_bytes(raw_email)
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")
            to_ = decode_header(msg.get("To"))[0]
            if isinstance(to_[0], bytes):
                to_ = to_[0].decode(to_[1] if to_[1] else "utf-8")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True)
                        break
            else:
                body = msg.get_payload(decode=True)
            body = decode_body(body)
            sent_emails.append({"subject": subject, "to": to_, "body": body})
            tts = gTTS(
                text=f"Subject: {subject}. To: {to_}. Body: {body[:300]}...",
                lang="en",
            )
            with NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                audio_path = fp.name
                tts.save(audio_path)
                fp.close()
            sent_emails[-1]["audio_path"] = audio_path
        return render(
            request,
            "homepage/sent.html",
            {
                "sent_emails": sent_emails,
                "message": f"You have {len(sent_emails)} emails in Sent folder. Content is being read aloud.",
            },
        )

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return HttpResponse(f"Failed to fetch emails: {str(e)}")

    finally:
        if conn:
            conn.logout()


def trash_view(request):
    email_address = config("EMAIL_ADDRESS")
    password = config("EMAIL_PASSWORD")

    if not email_address or not password:
        return redirect("homepage:login")

    try:
        conn = login_imap(email_address, password)
        conn.select('"[Gmail]/Trash"')
        result_trash, data_trash = conn.search(None, "ALL")
        trash_list = data_trash[0].split()
        no_trash = len(trash_list)

        if no_trash == 0:
            return render(
                request, "homepage/trash.html", {"message": "Trash folder is empty."}
            )

        trash_emails = []
        for email_id in trash_list:
            result, email_data = conn.fetch(email_id, "(RFC822)")
            raw_email = email_data[0][1]
            msg = message_from_bytes(raw_email)
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")
            from_ = decode_header(msg.get("From"))[0]
            if isinstance(from_[0], bytes):
                from_ = from_[0].decode(from_[1] if from_[1] else "utf-8")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True)
                        break
            else:
                body = msg.get_payload(decode=True)
            body = decode_body(body)
            trash_emails.append({"subject": subject, "from": from_, "body": body})
            tts = gTTS(
                text=f"Subject: {subject}. From: {from_}. Body: {body[:300]}...",
                lang="en",
            )
            with NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                audio_path = fp.name
                tts.save(audio_path)
                fp.close()
            trash_emails[-1]["audio_path"] = audio_path
        return render(
            request,
            "homepage/trash.html",
            {
                "trash_emails": trash_emails,
                "message": f"You have {no_trash} emails in the Trash folder.",
            },
        )

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return HttpResponse(f"Failed to fetch emails: {str(e)}")

    finally:
        if conn:
            conn.logout()
