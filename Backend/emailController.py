import smtplib
from email.mime.text import MIMEText
import emailAuthInfo

sender_email, password = emailAuthInfo.getEmailAndPassword()

def sendMail(email, text):
    message = MIMEText(text)
    message["Subject"] = "Neu Frage gestellt. Bitte eine Rückmeldung!"
    message["From"] = sender_email
    message["To"] = email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, email, message.as_string())

def sendEmailToAdmin(question_id, email, question):
    text = f'Sehr geehrte Damen und Herren,\n ' \
           f'Der User mit der Mail-Adresse {email} hat die folgende Frage gestellt: \n\n' \
           f'{question} \n\n' \
           f'Klicken Sie auf dem folgenden Link, um die Frage zu bearbeiten: ' \
           f'www.haraldritz.de/chatbot/question/{question_id}\n\n' \
           f'Viele Grüße,\n' \
           f'IOO Chatbot'
    sendMail(sender_email, text)

def sendAnswerPerMail(email, question, answer):
    text = "Sehr geehrte Damen und Herren,\n" \
           f'Die Antwort zu Ihrer Frage: "{question}" lautet wie folgendes: \n\n' \
           f'{answer[0]} \n' \
           f'Links dazu: {", ".join(answer[1])} \n' \
           f'Falls Sie weitere fragen haben, können Sie das Chatbot "IOOChatbot" nutzen ' \
           f'oder eine Mail an die Sekretariat schicken.\n\n' \
           f'Viele Grüße, \n' \
           f'Fachbereich MND'
    sendMail(email, text)

# if __name__ == '__main__':
#     sendEmailToAdmin("elisbardhi@hotmail.com", "534trg0mn3bv4tt","Wann finden die Sprechstunden mit Herr Ritz statt?")
#     sendAnswerPerMail("elisbardhi@hotmail.com","Wann finden die Sprechstunden mit Herr Ritz statt?", ["Montag - Freitag, 8 - 9 Uhr",["www.google.com", "www.yahoo.com"]])