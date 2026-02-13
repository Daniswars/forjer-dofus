import os
from dotenv import load_dotenv
from email.message import EmailMessage
import ssl
import smtplib


def send_mail(item, exito):
    load_dotenv()

    email_sender = "daniswarsxy2@gmail.com"
    email_receiver = email_sender
    password = "lombioddhdsxmnaf"

    # Adaptación para aceptar los mensajes actuales de main
    if exito == "10 intentos":
        subject = "10 intentos llevados a cabo"
        body = f"{item} se está magueando"
    elif exito == "inicio magueo":
        subject = "Magueo iniciado"
        body = f"{item} se está magueando"
    elif exito == "Finalizar forzado":
        subject = "Programa finalizado"
        body = f"{item} se ha finalizado"
    elif exito == "¡Éxito!":
        subject = "Éxito PA"
        body = f"{item} ha sido magueado"
    elif exito == "Sin runas":
        subject = "Sin runas"
        body = "Compra runas perro"
    else:
        subject = str(exito)
        body = f"{item} - {exito}"

    em = EmailMessage()
    em["From"] = email_sender
    em["To"] = email_receiver
    em["Subject"] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(email_sender, password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())