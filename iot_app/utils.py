import json

def parse_sensor_value(text: str) -> float | None:
    """
    Trích xuất giá trị số từ chuỗi đầu vào (JSON, float, hoặc key=value).
    Trả về số thực (float) nếu tìm thấy, ngược lại trả về None.
    """
    if not text:
        return None

    # 1. Thử parse dạng JSON trước
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            # Nếu có key rõ ràng như "value", "temp", "temperature", "hum", "humidity", ưu tiên lấy.
            for key in ["value", "temp", "temperature", "hum", "humidity"]:
                if key in data and isinstance(data[key], (int, float)) and not isinstance(data[key], bool):
                    return float(data[key])
            
            # Quét tìm giá trị số đầu tiên
            for k, v in data.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    return float(v)
            return None
        elif isinstance(data, (int, float)) and not isinstance(data, bool):
            return float(data)
    except Exception:
        pass

    # 2. Thử parse trực tiếp thành một số
    try:
        return float(text)
    except Exception:
        pass

    # 3. Thử parse dạng key=value (VD: temp=30.5)
    if "=" in text:
        try:
            k, v = text.split("=", 1)
            return float(v.strip())
        except Exception:
            pass

    return None
