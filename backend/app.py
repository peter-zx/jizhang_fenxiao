import streamlit as st
import pandas as pd
from datetime import date
from database import engine, Base, SessionLocal
from models import SalesPerson, Product

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

st.set_page_config(page_title="记账核算工具", layout="wide")

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

def go_home():
    st.session_state.current_page = "home"

def go_detail(person_id):
    st.session_state.current_page = "detail"
    st.session_state.selected_person_id = person_id

db = SessionLocal()

if st.session_state.current_page == "home":
    st.title("分销记账核算工具")
    
    total_persons = db.query(SalesPerson).count()
    total_target = db.query(SalesPerson).all()
    total_target_amount = sum(p.target_amount for p in total_target)
    
    all_products = db.query(Product).all()
    total_delivered_amount = sum(p.amount for p in all_products if p.is_delivered)
    total_delivered_count = sum(1 for p in all_products if p.is_delivered)
    total_product_count = len(all_products)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("销售员人数", total_persons)
    col2.metric("目标总金额", f"¥{total_target_amount:,.0f}")
    col3.metric("已完成金额", f"¥{total_delivered_amount:,.0f}", 
                delta=f"{total_delivered_count}/{total_product_count}")
    
    st.divider()
    st.subheader("销售员列表")
    
    persons = db.query(SalesPerson).all()
    
    if not persons:
        st.info("暂无销售员数据，请导入或添加数据")
    else:
        cols = st.columns(min(len(persons), 3))
        for idx, person in enumerate(persons):
            products = db.query(Product).filter(Product.salesperson_id == person.id).all()
            delivered_count = sum(1 for p in products if p.is_delivered)
            delivered_amount = sum(p.amount for p in products if p.is_delivered)
            total_amount = sum(p.amount for p in products)
            
            with cols[idx % 3]:
                with st.container():
                    st.markdown(f"**{person.name}**")
                    st.write(f"进度: {delivered_count}/{len(products)}")
                    st.write(f"金额: ¥{delivered_amount:,.0f} / ¥{total_amount:,.0f}")
                    st.write(f"目标: ¥{person.target_amount:,.0f}")
                    if st.button("查看详情", key=f"btn_{person.id}"):
                        go_detail(person.id)
    
    st.divider()
    st.subheader("数据管理")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**导入数据**")
        uploaded_file = st.file_uploader("上传Excel", type=["xlsx"], key="import")
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            st.dataframe(df)
            if st.button("确认导入"):
                for _, row in df.iterrows():
                    person = db.query(SalesPerson).filter(SalesPerson.name == row["销售员"]).first()
                    if not person:
                        person = SalesPerson(name=row["销售员"], target_amount=0)
                        db.add(person)
                        db.commit()
                    
                    product = Product(
                        salesperson_id=person.id,
                        name=row["产品"],
                        amount=row["金额"],
                        is_delivered=False,
                        created_date=date.today()
                    )
                    db.add(product)
                db.commit()
                st.success("导入成功")
                st.rerun()
    
    with col2:
        st.write("**导出数据**")
        if st.button("导出Excel"):
            data = []
            for p in db.query(SalesPerson).all():
                products = db.query(Product).filter(Product.salesperson_id == p.id).all()
                for prod in products:
                    data.append({
                        "销售员": p.name,
                        "产品": prod.name,
                        "金额": prod.amount,
                        "已交付": "是" if prod.is_delivered else "否"
                    })
            df = pd.DataFrame(data)
            df.to_excel("sales_data.xlsx", index=False)
            st.success("已导出到 sales_data.xlsx")
    
    with col3:
        st.write("**添加销售员**")
        new_name = st.text_input("姓名", key="new_name")
        new_target = st.number_input("目标金额", min_value=0.0, key="new_target")
        if st.button("添加"):
            if new_name:
                person = SalesPerson(name=new_name, target_amount=new_target)
                db.add(person)
                db.commit()
                st.success(f"已添加 {new_name}")
                st.rerun()

elif st.session_state.current_page == "detail":
    person = db.query(SalesPerson).filter(SalesPerson.id == st.session_state.selected_person_id).first()
    
    if st.button("← 返回首页"):
        go_home()
        st.rerun()
    
    products = db.query(Product).filter(Product.salesperson_id == person.id).all()
    delivered_amount = sum(p.amount for p in products if p.is_delivered)
    
    st.title(f"{person.name}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("目标金额", f"¥{person.target_amount:,.0f}")
    col2.metric("已完成", f"¥{delivered_amount:,.0f}")
    col3.metric("完成率", f"{delivered_amount/person.target_amount*100:.1f}%" if person.target_amount > 0 else "0%")
    
    st.divider()
    st.subheader("产品列表")
    
    for prod in products:
        col1, col2, col3 = st.columns([4, 2, 1])
        with col1:
            st.write(f"**{prod.name}**  ¥{prod.amount:,.0f}")
        with col2:
            status = "✓ 已交付" if prod.is_delivered else "○ 未交付"
            st.write(status)
        with col3:
            if st.button("切换", key=f"toggle_{prod.id}"):
                prod.is_delivered = not prod.is_delivered
                db.commit()
                st.rerun()
    
    st.divider()
    st.subheader("添加产品")
    col1, col2, col3 = st.columns(3)
    with col1:
        prod_name = st.text_input("产品名称", key="prod_name")
    with col2:
        prod_amount = st.number_input("金额", min_value=0.0, key="prod_amount")
    if st.button("添加产品"):
        if prod_name:
            product = Product(
                salesperson_id=person.id,
                name=prod_name,
                amount=prod_amount,
                is_delivered=False,
                created_date=date.today()
            )
            db.add(product)
            db.commit()
            st.success("已添加")
            st.rerun()

db.close()
