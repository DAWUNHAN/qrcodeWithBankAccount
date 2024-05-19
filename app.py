from flask import Flask, request, render_template, url_for
import qrcode
from io import BytesIO
import base64
from urllib.parse import quote
from dotenv import load_dotenv
import os

# .env 파일의 환경 변수 로드
load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    bank_name = request.form['bank_name']
    account_number = request.form['account_number']

    print(f"Received bank_name: {bank_name}, account_number: {account_number}")

    if not bank_name or not account_number:
        return render_template('index.html', error="Bank name or account number is missing.")

    if not account_number.isdigit():
        return render_template('index.html', error="Account number must be numeric.")

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
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    img_data = f"data:image/png;base64,{img_base64}"

    return render_template('index.html', qr_code=img_data)

@app.route('/copy_to_clipboard')
def copy_to_clipboard():
    data = request.args.get('data', '')
    return render_template('copy.html', data=data)

if __name__ == '__main__':
    host = os.getenv('FLASK_APP_HOST')
    port = int(os.getenv('FLASK_APP_PORT'))
    app.run(debug=True, host=host, port=port)
