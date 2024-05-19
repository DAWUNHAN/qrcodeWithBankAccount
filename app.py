from flask import Flask, request, render_template, send_file, url_for
import qrcode
from io import BytesIO
import base64
from urllib.parse import quote
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from dotenv import load_dotenv
import os

# .env 파일의 환경 변수 로드
load_dotenv()

app = Flask(__name__)

# 한글 폰트 등록
pdfmetrics.registerFont(TTFont('NanumGothic', 'static/fonts/NanumGothic.ttf'))

def mask_account_holder(name):
    if len(name) == 2:
        return name[0] + "*"
    elif len(name) > 2:
        return name[0] + "*" + name[2:]
    return name

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    global qr_image_buffer  # Add this line to declare qr_image_buffer as global
    global bank_name, account_number, account_holder, masked_account_holder  # Declare these as global variables
    bank_name = request.form['bank_name']
    account_number = request.form['account_number']
    account_holder = request.form['account_holder']
    masked_account_holder = mask_account_holder(account_holder)

    print(f"Received bank_name: {bank_name}, account_number: {account_number}, account_holder: {account_holder}")

    if not bank_name or not account_number or not account_holder:
        return render_template('index.html', error="Bank name, account number or account holder is missing.")

    if not account_number.isdigit():
        return render_template('index.html', error="Account number must be numeric.")

    # QR 코드 데이터 설정: '계좌번호 은행명' 순서
    qr_data = f"{account_number} {bank_name}"
    print(f"QR Data: {qr_data}")

    # 데이터 값을 URL 인코딩
    encoded_data = quote(qr_data)

    # 환경 변수에서 IP 주소와 포트 가져오기
    local_ip = os.getenv('LOCAL_IP')
    port = os.getenv('FLASK_APP_PORT')

    # IP 주소와 포트를 직접 지정하여 URL 생성
    url = f"http://{local_ip}:{port}/copy_to_clipboard?data={encoded_data}"
    print(f"URL for QR: {url}")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    qr_image_buffer = BytesIO()
    img.save(qr_image_buffer, format="PNG")
    qr_image_buffer.seek(0)

    img_base64 = base64.b64encode(qr_image_buffer.getvalue()).decode('utf-8')
    img_data = f"data:image/png;base64,{img_base64}"

    return render_template('index.html', qr_code=img_data)

@app.route('/download_qr')
def download_qr():
    global qr_image_buffer, bank_name, account_number, account_holder, masked_account_holder  # Declare these as global variables
    qr_image_buffer.seek(0)  # Reset buffer position to the beginning

    # Create a PDF buffer
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)

    # Set font and size
    c.setFont("NanumGothic", 30)

    # Calculate positions for centering
    page_width, page_height = A4
    text = f"{account_number} {bank_name}"
    text_width = c.stringWidth(text, "NanumGothic", 30)
    text_x = (page_width - text_width) / 2

    masked_text = f"({masked_account_holder})"
    masked_text_width = c.stringWidth(masked_text, "NanumGothic", 30)
    masked_text_x = (page_width - masked_text_width) / 2

    qr_code_size = 400
    qr_code_x = (page_width - qr_code_size) / 2

    # Draw text on the PDF
    text_y = 780  # Set the y position of the text
    c.drawString(text_x, text_y, text)
    c.drawString(masked_text_x, text_y - 40, masked_text)

    # Draw the QR code on the PDF
    qr_image_path = "/tmp/qr_code.png"
    with open(qr_image_path, "wb") as f:
        f.write(qr_image_buffer.getvalue())
    c.drawImage(qr_image_path, qr_code_x, text_y - 500, qr_code_size, qr_code_size)  # Adjust position and size of the QR code

    # Save the PDF
    c.showPage()
    c.save()

    pdf_buffer.seek(0)

    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='qr_code.pdf')

@app.route('/copy_to_clipboard')
def copy_to_clipboard():
    data = request.args.get('data', '')
    return render_template('copy.html', data=data)

if __name__ == '__main__':
    host = os.getenv('FLASK_APP_HOST')
    port = int(os.getenv('FLASK_APP_PORT'))
    app.run(debug=True, host=host, port=port)
