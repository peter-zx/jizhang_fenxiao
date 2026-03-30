from database import engine, Base, SessionLocal
from models import SalesPerson, Product
from datetime import date

Base.metadata.create_all(bind=engine)

db = SessionLocal()

db.query(Product).delete()
db.query(SalesPerson).delete()

persons_data = [
    {"name": "张三", "target": 100000},
    {"name": "李四", "target": 80000},
    {"name": "王五", "target": 90000},
]

products_data = {
    "张三": ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10"],
    "李四": ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08"],
    "王五": ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11", "C12"],
}

for p in persons_data:
    person = SalesPerson(name=p["name"], target_amount=p["target"])
    db.add(person)
db.commit()

for name, products in products_data.items():
    person = db.query(SalesPerson).filter(SalesPerson.name == name).first()
    for i, prod_name in enumerate(products):
        product = Product(
            salesperson_id=person.id,
            name=f"产品{prod_name}",
            amount=2200,
            is_delivered=False,
            created_date=date.today()
        )
        db.add(product)

db.commit()
print("测试数据已初始化")
db.close()
