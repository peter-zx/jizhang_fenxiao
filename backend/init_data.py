from database import engine, Base, SessionLocal
from models import SalesPerson, Product
from datetime import date, timedelta

Base.metadata.create_all(bind=engine)

db = SessionLocal()

db.query(Product).delete()
db.query(SalesPerson).delete()

persons_data = ["张三", "李四", "王五"]

for name in persons_data:
    person = SalesPerson(name=name, target_amount=0)
    db.add(person)
db.commit()

products_info = {
    "张三": [("产品A01", 2200), ("产品A02", 3000), ("产品A03", 2500)],
    "李四": [("产品B01", 2800), ("产品B02", 2200)],
    "王五": [("产品C01", 3000), ("产品C02", 2600), ("产品C03", 2400)],
}

for name, products in products_info.items():
    person = db.query(SalesPerson).filter(SalesPerson.name == name).first()
    for prod_name, param_a in products:
        product = Product(
            salesperson_id=person.id,
            name=prod_name,
            years="1年",
            product_type="肢体",
            grade="2级",
            param_a=param_a,
            production_date=date.today(),
            expire_date=date.today() + timedelta(days=365),
            seal_date=date.today(),
            seal_expire_date=date.today() + timedelta(days=365),
            contact="13800138000",
            address="北京市",
            emergency_contact="13900139000",
            remark="",
            is_approved=True,
            is_delivered=False,
            created_date=date.today()
        )
        db.add(product)
    db.commit()

for person in db.query(SalesPerson).all():
    products = db.query(Product).filter(Product.salesperson_id == person.id).all()
    person.target_amount = sum(p.param_a - 800 for p in products)
db.commit()

print("测试数据已初始化")
print("公式: 产品金额 = 参数A - 800")
db.close()
