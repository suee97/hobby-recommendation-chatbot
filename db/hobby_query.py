from sqlalchemy import create_engine, text

DB_USER = 'ssafy'
DB_PASSWORD = 'ssafy'
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'ssafydb'

engine = create_engine(
    f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
)

def get_hobby_by_name(name: str):
    with engine.connect() as conn:
        query = text("""
            SELECT description, DetailedDescription, Equipment
            FROM hobbies
            WHERE name = :name
        """)
        result = conn.execute(query, {"name": name}).fetchone()
        return result

if __name__ == "__main__":
    # 테스트용
    hobby_name = "등산"  
    res = get_hobby_by_name(hobby_name)
    if res:
        print(f"Description: {res.description}")
        print(f"DetailedDescription: {res.DetailedDescription}")
        print(f"Equipment: {res.Equipment}")
    else:
        print(f"'{hobby_name}'에 해당하는 취미 정보가 없습니다.")