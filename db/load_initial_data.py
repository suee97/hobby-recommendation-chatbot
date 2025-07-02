# pip install pandas sqlalchemy pymysql cryptography

import pandas as pd
from sqlalchemy import create_engine, text
import os

# MySQL 연결 설정
DB_USER = 'ssafy'      
DB_PASSWORD = 'ssafy' 
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'ssafydb'   

engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4')

# 데이터베이스 및 테이블 생성 
init_sql = """
CREATE DATABASE IF NOT EXISTS ssafydb;
USE ssafydb;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    description TEXT,
    enjoys_physical_activity FLOAT,
    values_social_belonging FLOAT,
    likes_adventure FLOAT,
    creative_artistic_sense FLOAT,
    competitive_achievement_oriented FLOAT,
    needs_stress_relief FLOAT,
    values_learning_growth FLOAT,
    needs_recognition FLOAT,
    good_concentration FLOAT,
    trend_sensitive FLOAT,
    willing_to_pay_for_hobby FLOAT,
    likes_long_immersion FLOAT,
    likes_tangible_results FLOAT,
    likes_digital_tools FLOAT,
    prefers_spontaneous_activity FLOAT,
    sex_encoded INT,
    I_or_E_encoded INT,
    N_or_S_encoded INT,
    F_or_T_encoded INT,
    P_or_J_encoded INT,
    age_encoded INT,
    living_env_1 INT,
    living_env_2 INT,
    living_env_3 INT,
    living_env_4 INT,
    living_env_5 INT,
    living_env_6 INT,
    occupation_1 INT,
    occupation_2 INT,
    occupation_3 INT,
    occupation_4 INT,
    occupation_5 INT,
    occupation_6 INT,
    occupation_7 INT,
    occupation_8 INT,
    occupation_9 INT,
    occupation_10 INT,
    occupation_11 INT,
    occupation_12 INT,
    occupation_13 INT,
    current_favorite_hobby VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS hobbies (
    hobby_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    image_url VARCHAR(500),
    description TEXT,
    Active FLOAT,
    Physical FLOAT,
    RequiresFocus FLOAT,
    Indoor FLOAT,
    Outdoor FLOAT,
    RequiresTravel FLOAT,
    Solo FLOAT,
    `Group` FLOAT,
    SocialInteraction FLOAT,
    Creative FLOAT,
    Intellectual FLOAT,
    Emotional FLOAT,
    Analytical FLOAT,
    StressRelief FLOAT,
    CostRequired FLOAT,
    EquipmentRequired FLOAT,
    LearningRequired FLOAT,
    TimeRequired FLOAT,
    Challenging FLOAT,
    Competitive FLOAT,
    Rewarding FLOAT,
    Trendy FLOAT,
    RequiresConsistency FLOAT,
    ManualSkill FLOAT,
    InNature FLOAT,
    DetailedDescription TEXT,
    Equipment TEXT
);
"""

# DB 생성 및 테이블 생성 
with engine.connect() as conn:
    for stmt in init_sql.strip().split(';'):
        if stmt.strip():
            conn.execute(text(stmt))

# 테이블이 생성된 DB에 연결
engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4')

# CSV 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'db', 'data')

user_csv_path = os.path.join(DATA_DIR, 'user_hobbies_data - user_hobbies_data.csv')
hobby_csv_path = os.path.join(DATA_DIR, 'hobbies_data - hobbies_data.csv')

# CSV 불러오기
user_df = pd.read_csv(user_csv_path)
hobby_df = pd.read_csv(hobby_csv_path)

# 데이터 삽입
hobby_df.to_sql(name='hobbies', con=engine, if_exists='append', index=False)
user_df.to_sql(name='users', con=engine, if_exists='append', index=False)

print("데이터 삽입")