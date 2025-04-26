from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
import joblib  # để lưu và load model
import numpy as np
import pandas as pd

app = FastAPI()

# --- Load model, scaler, encoder, ... đã train ---
bundle = joblib.load('model_bundle.pkl')

# --- Định nghĩa schema dữ liệu đầu vào ---
class InputData(BaseModel):
    price: float
    area: float
    province_city: str
    district: str
    ward: str

# Func predict
def predict_anomaly(input_df, encoders, scaler, model, ward_avg_price_per_m2, district_avg_price_per_m2):
    df = input_df.copy()

    # Bước 1: Feature Engineering
    df['price_per_m2'] = df['price'] / df['area']

    # Tổ hợp district_ward để encode sau
    df['district_ward'] = df['district'] + "_" + df['ward']

    # Tương tác
    for col in ['province_city', 'district', 'ward', 'district_ward']:
        if df[col][0] not in encoders[col].classes_:
            return {"error": f"⚠️ Giá trị '{df[col][0]}' chưa từng thấy trong encoder '{col}'"}
        df[col] = encoders[col].transform(df[col])

    # Các đặc trưng tương tác
    df['area_x_district'] = df['area'] * df['district']
    df['price_per_m2_x_district'] = df['price_per_m2'] * df['district']
    df['price_per_m2_error_vs_ward_avg'] = df['price_per_m2'] - df['ward'].map(ward_avg_price_per_m2)
    df['price_per_m2_error_vs_district_avg'] = df['price_per_m2'] - df['district'].map(district_avg_price_per_m2)

    # Chọn các đặc trưng cần cho model
    selected_features = [
        'price_per_m2',
        'district',
        'ward',
        'district_ward',
        'area',
        'area_x_district',
        'price_per_m2_x_district',
        'price_per_m2_error_vs_ward_avg',
        'price_per_m2_error_vs_district_avg'
    ]

    df_model = df[selected_features]

    # Bước 2: Scale
    df_scaled = scaler.transform(df_model)

    # Bước 3: Anomaly score & kết quả
    score = model.decision_function(df_scaled)[0]

    # Phân loại theo score
    if score > 0.1:
        risk = "✅ Rất an toàn"
        level = 0
    elif score > 0.05:
        risk = "✅ Bình thường"
        level = 1
    elif score > 0:
        risk = "⚠️ Hơi nghi ngờ"
        level = 2
    else:
        risk = "🚨 Bất thường rõ ràng"
        level = 3

    all_data = pd.read_csv('./EDA/final_data.csv')
    data_same_place_district = all_data[
        (encoders['province_city'].transform(all_data['province_city']) ==  df['province_city'][0]) & 
        (encoders['district'].transform(all_data['district']) == df['district'][0])
    ]
    data_same_place_ward = data_same_place_district[
        (encoders['ward'].transform(data_same_place_district['ward']) == df['ward'][0])
    ]

    return {
        "anomaly_score": round(score, 5),
        "risk": {
            "risk_level": level,
            "risk_label": risk
        },
        "explanation": {
            'avg_price': {
                'ward_avg_price_per_m2': df['ward'].map(ward_avg_price_per_m2)[0],
                'district_avg_price_per_m2': df['district'].map(district_avg_price_per_m2)[0]
            },
            'other_motel_room_same_district': data_same_place_district.replace([np.inf, -np.inf, np.nan], None).to_dict(orient='records'),
            'other_motel_room_same_ward': data_same_place_ward.replace([np.inf, -np.inf, np.nan], None).to_dict(orient='records')
        }
    }

# --- Endpoint predict ---
@app.post("/predict")
def make_prediction(data: List[InputData]):
    input = [item.model_dump() for item in data]
    df_input = pd.DataFrame(input)

    result = predict_anomaly(df_input, **bundle)

    return {'prediction': result}