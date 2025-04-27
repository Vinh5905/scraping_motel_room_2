from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
import joblib  # để lưu và load model
import numpy as np
import pandas as pd
import pickle
import json
import os
import getpass
import pickle
import requests
import zipfile
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
import dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

app = FastAPI()

# --- Load model, scaler, encoder, ... đã train ---
bundle = joblib.load('model_bundle.pkl')

# All data
all_data = pd.read_csv('./EDA/final_data.csv')

# Data text
data_text = pd.read_csv('./RAG_langchain/data_text.csv')

# LLM
dotenv.load_dotenv()
if "TOGETHER_API_KEY" not in os.environ or not os.environ["TOGETHER_API_KEY"]:
    os.environ["TOGETHER_API_KEY"] = getpass("Nhập Together API Key: ")
llm = init_chat_model("meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", model_provider="together") 

# Prompt Template
system_prompt = """Bạn là một trợ lý tìm kiếm bất động sản.
Sử dụng thông tin dưới đây (dạng JSON) để trả lời câu hỏi ngắn gọn dưới 3 câu.
Nếu có thể, tạo một list ID các mã như ["id1", "id2", ...].
Nếu không tìm thấy thông tin liên quan, hãy trả lời [].

Thông tin:\n{retrieved_text}"""

custom_rag_prompt = PromptTemplate.from_template(system_prompt)

def download_vectorstore():
    if not os.path.exists("vector_store.pkl"):
        print("Downloading vectorstore.pkl...")
        url = "https://huggingface.co/spaces/KevinPhamH/my-vectorstore/resolve/main/vector_store.pkl"
        response = requests.get(url)
        
        with open("vector_store.pkl", "wb") as f:
            f.write(response.content)
        
        print("Download completed.")
    else:
        print("vectorstore.pkl already exists.")

download_vectorstore()

with open("vector_store.pkl", 'rb') as f:
    vector_store = pickle.load(f)

# --- Định nghĩa schema dữ liệu đầu vào ---
class InputData(BaseModel):
    price: float
    area: float
    province_city: str
    district: str
    ward: str

class DistrictData(BaseModel):
    district: str

class SearchData(BaseModel):
    query: str

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


@app.get("/all_districts")
def get_districts():
    all_districts = list(all_data['district'].unique())

    return {
        'data': {
            'label': ['Quận', 'Huyện'],
            'districts': all_districts
        }
    }


@app.post("/all_wards_in_district")
def get_all_wards_in_district(district: DistrictData):
    district = district.model_dump()['district']

    all_wards_in_district = list(all_data.loc[all_data['district'] == district, 'ward'].unique())

    return {
        'data': {
            'district': {
                'name': district,
                'all_wards_in_district': all_wards_in_district
            }
        }
    }


@app.get("/all_wards")
def get_wards():
    all_wards = list(all_data['ward'].unique())

    return {
        'data': {
            'label': ['Phường', 'Xã', 'Thị trấn'],
            'wards': all_wards
        }
    }
    
@app.post("/search_smart")
def search_smart(query: SearchData):
    query = query.model_dump()['query']

    results = vector_store.similarity_search(query, k=20)

    result_ids = [doc.metadata['id'] for doc in results]
    result_data_text = data_text.loc[data_text['id'].isin(result_ids), 'text'].to_list()
    retrieved_text = ",\n".join(result_data_text)

    formatted_prompt = custom_rag_prompt.format(retrieved_text=retrieved_text) 

    final_answer = llm.invoke([
        SystemMessage(content=formatted_prompt),
        HumanMessage(content=query)
    ]) 

    filter_ids = json.loads(final_answer.content)

    data = all_data[all_data['merge_file_id'].isin(filter_ids)]

    return {
        'data': {
            'all_data_found': data.replace([np.inf, -np.inf, np.nan], None).to_dict(orient='records')
        }
    }
