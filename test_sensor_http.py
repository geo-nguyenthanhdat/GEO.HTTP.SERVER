import urllib.request, urllib.error, urllib.parse, json, time, random

BASE_URL = "http://127.0.0.1:8000/api"
USERNAME = "sensor_bot"
PASSWORD = "botpassword123"
DEVICE_NAME = "nhiet_do_01"

print(f"1. Đăng ký tài khoản ảo ({USERNAME})...")
try:
    req = urllib.request.Request(f"{BASE_URL}/register", data=json.dumps({"username": USERNAME, "password": PASSWORD}).encode(), headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    # Nếu báo lỗi vì trùng user thì bỏ qua
    pass
except Exception as e:
    print("Không thể kết nối Server API. Server có đang tắt không?", e)
    exit(1)

print("2. Đăng nhập để lấy Token...")
data = urllib.parse.urlencode({'username': USERNAME, 'password': PASSWORD}).encode()
req = urllib.request.Request(f"{BASE_URL}/login", data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
try:
    with urllib.request.urlopen(req) as response:
        token = json.loads(response.read().decode())['access_token']
except Exception as e:
    print("Đăng nhập thất bại!", e)
    exit(1)

print(f"3. Bắt đầu đẩy dữ liệu ảo lên thiết bị '{DEVICE_NAME}' mỗi 3 giây...")
print("Hãy mở trình duyệt, đăng nhập dưới tư cách Admin hoặc user 'sensor_bot' để xem bảng dữ liệu tự động Update real-time nhé!")
try:
    while True:
        value = round(random.uniform(22.0, 28.5), 2)
        payload = json.dumps({"value": value}).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/data/{DEVICE_NAME}",
            data=payload,
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'},
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            print(f"Đã bắn dữ liệu {value} lên server HTTP API!")
        time.sleep(3)
except KeyboardInterrupt:
    print("\nĐã dừng bắn dữ liệu.")
