# config.py
TELE_TOKEN = "8917951413:AAE6LKUEfYEYiQrFWGoKsQn0tumZc_XbcHg"
TELE_CHAT_ID = "7290661009"

VPD_THRESHOLDS_SMART = {
    "Sáng":   {"start": 6,  "end": 10, "min": 0.6, "max": 1.0},
    "Trưa":   {"start": 10, "end": 14, "min": 1.0, "max": 1.5},
    "Chiều":  {"start": 14, "end": 18, "min": 0.7, "max": 1.2},
    "Tối":    {"start": 18, "end": 22, "min": 0.5, "max": 0.8},
    "Khuya":  {"start": 22, "end": 6,  "min": 0.3, "max": 0.6},
}
