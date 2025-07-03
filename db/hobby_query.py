from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

# MySQL 연결 설정
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD') 
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME') 

engine = create_engine(
    f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
)

def get_hobby_by_name(name: str):
    with engine.connect() as conn:
        query = text("""
            SELECT image_url, description, DetailedDescription, Equipment
            FROM hobbies
            WHERE name = :name
        """)
        result = conn.execute(query, {"name": name}).fetchone()
        return result

def get_all_hobby_names():
    with engine.connect() as conn:
        query = text("""
            SELECT name
            FROM hobbies
        """)
        result = conn.execute(query).fetchall()
        return result

if __name__ == "__main__":
    # 테스트용
    hobby_name = "등산"  
    res = get_hobby_by_name(hobby_name)
    if res:
        print(f"image_url: {res.image_url}")
        print(f"Description: {res.description}")
        print(f"DetailedDescription: {res.DetailedDescription}")
        print(f"Equipment: {res.Equipment}")
    else:
        print(f"'{hobby_name}'에 해당하는 취미 정보가 없습니다.")