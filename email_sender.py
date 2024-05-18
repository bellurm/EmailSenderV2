# cyberworm
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import optparse as opt

class EmailSender():
    def __init__(self):
        self.RED = '\033[91m'
        self.GREEN = '\033[92m'
        self.RESET = '\033[0m'

        parse_object = opt.OptionParser(
            f"""{self.RED}
                MADE BY CYBERWORM
                Contact: https://blog-cyberworm.com/blog/social-media
                USAGE 1: python email_sender.py -s <your email address> -p <your e-mail's password> -r <the receiver's e-mail address>
                USAGE 2: python email_sender.py --sender-email <your email address> --password <your e-mail's password> --receiver-email <the receiver's e-mail address>
                {self.RESET}
            """
        )
        parse_object.add_option("-s", "--sender-email", dest="sender_email")
        parse_object.add_option("-p", "--password", dest="password")
        parse_object.add_option("-r", "--receiver-email", dest="receiver_email")

        (self.value, self.key) = parse_object.parse_args()
        self.sender_email = self.value.sender_email
        self.password = self.value.password
        self.receiver_email = self.value.receiver_email

        print(self.sender_email, self.password, self.receiver_email)

    def createMessage(self, subject, text):
        self.message = MIMEMultipart()
        self.message["Subject"] = subject
        self.message["From"] = self.sender_email
        self.message["To"] = self.receiver_email
        
        part1 = MIMEText(text, "plain")
        self.message.attach(part1)
    
    def sendMessageWithAttachment(self, filepath):
        part2 = MIMEBase('application', "octet-stream")
        self.filepath = filepath
        self.filepath = input(f"{self.GREEN}path/to/your/file.ext: {self.RESET}")
        try:
            with open(self.filepath, "rb") as attachment:
                part2.set_payload(attachment.read())
            encoders.encode_base64(part2)
            part2.add_header('Content-Disposition', f'attachment; filename="{filepath.split("/")[-1]}"')
            self.message.attach(part2)
        except FileNotFoundError:
            print(f"{self.RED}Error: The file {self.filepath} was not found.{self.RESET}")
            exit(1)
        except Exception as e:
            print(f"{self.RED}An error occurred while reading the file: {e}.{self.RESET}")
            exit(1)

    
    def sendEmail(self, smtp_server):
        context = ssl.create_default_context()
        server = None
        try:
            server = smtplib.SMTP(smtp_server, 587)  # SMTP sunucusu ve portu
            server.starttls(context=context)
            server.login(self.sender_email, self.password)  # E-posta kimlik doğrulaması
            server.sendmail(self.sender_email, self.receiver_email, self.message.as_string())
            print(f"{self.GREEN}Email sent successfully!{self.RESET}")
        except smtplib.SMTPAuthenticationError:
            print(f"{self.RED}Error: Authentication failed, please check your email address and password.{self.RESET}")
        except smtplib.SMTPConnectError:
            print(f"{self.RED}Error: Failed to connect to the server. Check the server address and port.{self.RESET}")
        except Exception as e:
            print(f"{self.RED}An error occurred: {e}.{self.RESET}")
        finally:
            if server is not None:
                server.quit()
            
            
user = EmailSender()

subject = input(f"{user.GREEN}What is the Subject of your e-mail? > {user.RESET}")
text = input(f"{user.GREEN}What is your text that will be sent? > {user.RESET}")
user.createMessage(subject, text)

is_wanted = input(f"{user.GREEN}Do you want to add an attachment? (y/n)> {user.RESET}")
if is_wanted.lower() == "y":
    filepath = input(f"{user.GREEN}path/to/your/file.ext: {user.RESET}")
    user.sendMessageWithAttachment(filepath)

smtp_server = input(f"{user.GREEN}Enter your SMTP Server: {user.RESET}")
user.sendEmail(smtp_server)