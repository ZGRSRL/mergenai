import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from pathlib import Path

def send_email_with_pdf(pdf_filename, recipient_email):
    """PDF raporunu e-posta ile gönder"""
    try:
        # E-posta ayarları
        sender_email = "arl.zgr@gmail.com"  # Gönderen e-posta
        sender_password = "your_app_password"  # Uygulama şifresi (Gmail için)
        
        # E-posta oluştur
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "FLETC Artesia Lodging Services - Kapsamli Analiz Raporu"
        
        # E-posta içeriği
        body = """
Merhaba,

FLETC Artesia Off-Center Lodging Services ihalesi için yuklenen dokumanlarin kapsamli analizini 
tamamladim. Rapor, 9 dokumanin detayli analizini, kritik gereksinimleri, risk faktorlerini ve 
basarili teklif verme stratejilerini icermektedir.

Rapor ozeti:
- 9 dokumanin detayli analizi
- Kritik gereksinimler ve kisitlamalar
- Yangin guvenligi ve Davis-Bacon Act gereksinimleri
- Teklif stratejisi ve oneriler
- Risk analizi ve azaltma stratejileri

PDF raporu ekte bulunmaktadir.

Saygilarimla,
ZGR AI Analiz Sistemi
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # PDF dosyasını ekle
        if os.path.exists(pdf_filename):
            with open(pdf_filename, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {pdf_filename}',
            )
            msg.attach(part)
            print(f"PDF dosyasi eklendi: {pdf_filename}")
        else:
            print(f"PDF dosyasi bulunamadi: {pdf_filename}")
            return False
        
        # E-posta gönder
        print("E-posta gonderiliyor...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        print(f"E-posta basariyla gonderildi: {recipient_email}")
        return True
        
    except Exception as e:
        print(f"E-posta gonderme hatasi: {str(e)}")
        print("Not: Gmail icin 'App Password' kullanmaniz gerekiyor.")
        print("https://myaccount.google.com/apppasswords adresinden alabilirsiniz.")
        return False

def main():
    """Ana fonksiyon"""
    # En son oluşturulan PDF dosyasını bul
    pdf_files = list(Path(".").glob("FLETC_Artesia_Lodging_Detailed_Analysis_*.pdf"))
    
    if not pdf_files:
        print("PDF dosyasi bulunamadi!")
        return
    
    # En yeni dosyayı al
    latest_pdf = max(pdf_files, key=lambda x: x.stat().st_mtime)
    print(f"En yeni PDF dosyasi: {latest_pdf}")
    
    # E-posta gönder
    recipient_email = "arl.zgr@gmail.com"
    email_sent = send_email_with_pdf(str(latest_pdf), recipient_email)
    
    if email_sent:
        print("Rapor basariyla e-posta ile gonderildi!")
    else:
        print("E-posta gonderilemedi. PDF dosyasi hazir:")
        print(f"Dosya: {latest_pdf}")

if __name__ == "__main__":
    main()










