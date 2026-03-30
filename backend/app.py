import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import engine, Base, SessionLocal
from models import SalesPerson, Product, SystemConfig
import io

Base.metadata.create_all(bind=engine)

st.set_page_config(page_title="记账核算工具", layout="wide")

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

def navigate(page):
    st.session_state.current_page = page

def go_salesperson(person_id):
    st.session_state.current_page = "salesperson"
    st.session_state.selected_person_id = person_id
    st.session_state.salesperson_view = "preview"

db = SessionLocal()

config = db.query(SystemConfig).first()
if not config:
    config = SystemConfig(param_c=300, param_d=500)
    db.add(config)
    db.commit()

PARAM_C = config.param_c
PARAM_D = config.param_d
FORMULA_AMOUNT = PARAM_C + PARAM_D

ALL_COLUMNS = [
    "产品名字", "年限", "类型", "等级", "参数A",
    "生产日期", "过期时间", "盖章日期", "盖章过期时间",
    "联系方式", "地址", "紧急联系", "备注"
]
DEFAULT_COLUMNS = ["产品名字", "类型", "等级"]

def recalculate_target_amounts():
    for person in db.query(SalesPerson).all():
        products = db.query(Product).filter(Product.salesperson_id == person.id).all()
        person.target_amount = sum(p.amount for p in products)
    db.commit()

def check_duplicate_product(salesperson_id, product_name):
    existing = db.query(Product).filter(
        Product.salesperson_id == salesperson_id,
        Product.name == product_name
    ).first()
    return existing is not None

if st.session_state.current_page == "home":
    st.title("分销记账核算工具")
    
    total_persons = db.query(SalesPerson).count()
    all_persons = db.query(SalesPerson).all()
    total_target = sum(p.target_amount for p in all_persons)
    
    all_products = db.query(Product).all()
    total_delivered_amount = sum(p.amount for p in all_products if p.is_delivered)
    total_delivered_count = sum(1 for p in all_products if p.is_delivered)
    total_product_count = len(all_products)
    
    pending_approvals = db.query(Product).filter(Product.is_approved == False).count()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("销售员人数", total_persons)
    col2.metric("目标总金额", f"¥{total_target:,.0f}")
    col3.metric("已完成金额", f"¥{total_delivered_amount:,.0f}", 
                delta=f"{total_delivered_count}/{total_product_count}")
    col4.metric("待审批", pending_approvals, delta="需要处理" if pending_approvals > 0 else None)
    
    st.divider()
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➕ 新增销售员", width='stretch'):
            navigate("add_salesperson")
    with col_btn2:
        if st.button("📥 导出数据", width='stretch'):
            navigate("export")
    
    st.divider()
    st.subheader("销售员列表")
    
    persons = db.query(SalesPerson).all()
    
    if not persons:
        st.info("暂无销售员数据，请点击「新增销售员」添加")
    else:
        cols = st.columns(min(len(persons), 3))
        for idx, person in enumerate(persons):
            products = db.query(Product).filter(Product.salesperson_id == person.id).all()
            delivered_count = sum(1 for p in products if p.is_delivered)
            delivered_amount = sum(p.amount for p in products if p.is_delivered)
            task_amount = sum(p.amount for p in products)
            
            with cols[idx % 3]:
                with st.container():
                    st.markdown(f"**{person.name}**")
                    st.write(f"任务: ¥{task_amount:,.0f}")
                    st.write(f"完成: ¥{delivered_amount:,.0f} ({delivered_count}/{len(products)})")
                    if st.button("查看详情", key=f"btn_{person.id}"):
                        go_salesperson(person.id)

elif st.session_state.current_page == "add_salesperson":
    st.title("➕ 新增销售员")
    
    if st.button("← 返回首页"):
        navigate("home")
        st.rerun()
    
    st.divider()
    st.subheader("参数配置")
    
    with st.expander("系统参数 (参数C/D)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_c = st.number_input(f"参数C (默认{PARAM_C})", value=float(PARAM_C), min_value=0.0, step=10.0)
        with col2:
            new_d = st.number_input(f"参数D (默认{PARAM_D})", value=float(PARAM_D), min_value=0.0, step=10.0)
        
        if st.button("保存参数"):
            config.param_c = new_c
            config.param_d = new_d
            db.commit()
            st.success("参数已保存")
            st.rerun()
        
        st.info(f"产品金额 = 参数A - {new_c + new_d}")
    
    st.divider()
    st.subheader("新增销售员")
    
    new_name = st.text_input("销售员姓名", key="new_person_name")
    
    if st.button("添加"):
        if new_name:
            existing = db.query(SalesPerson).filter(SalesPerson.name == new_name).first()
            if existing:
                st.error(f"销售员「{new_name}」已存在！")
            else:
                person = SalesPerson(name=new_name, target_amount=0)
                db.add(person)
                db.commit()
                st.success(f"已添加「{new_name}」")
                go_salesperson(person.id)
        else:
            st.error("请输入销售员姓名")
    
    st.divider()
    st.subheader("已有销售员")
    
    persons = db.query(SalesPerson).all()
    for p in persons:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"{p.name}")
        with col2:
            st.write(f"任务: ¥{p.target_amount:,.0f}")
        with col3:
            if st.button("进入", key=f"enter_{p.id}"):
                go_salesperson(p.id)
    
    st.divider()
    st.subheader("参数A 审批管理")
    
    pending_products = db.query(Product).filter(Product.is_approved == False).all()
    
    if not pending_products:
        st.success("暂无待审批项目")
    else:
        for prod in pending_products:
            person = db.query(SalesPerson).filter(SalesPerson.id == prod.salesperson_id).first()
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.write(f"**{person.name}** - {prod.name}")
            with col2:
                st.write(f"参数A: {prod.param_a:,.0f}")
            with col3:
                st.write(f"金额: ¥{prod.amount:,.0f}")
            with col4:
                if st.button("批准", key=f"approve_{prod.id}"):
                    prod.is_approved = True
                    db.commit()
                    recalculate_target_amounts()
                    st.rerun()

elif st.session_state.current_page == "salesperson":
    person = db.query(SalesPerson).filter(SalesPerson.id == st.session_state.selected_person_id).first()
    
    if "salesperson_view" not in st.session_state:
        st.session_state.salesperson_view = "preview"
    
    products = db.query(Product).filter(Product.salesperson_id == person.id).all()
    delivered_amount = sum(p.amount for p in products if p.is_delivered)
    task_amount = sum(p.amount for p in products)
    
    col_header1, col_header2, col_header3 = st.columns([1, 1, 1])
    with col_header1:
        if st.button("← 返回首页"):
            navigate("home")
            st.rerun()
    with col_header2:
        if st.button("📋 预览模式"):
            st.session_state.salesperson_view = "preview"
            st.rerun()
    with col_header3:
        if st.button("✏️ 编辑模式"):
            st.session_state.salesperson_view = "edit"
            st.rerun()
    
    st.title(f"{person.name}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("任务金额", f"¥{task_amount:,.0f}")
    col2.metric("已完成", f"¥{delivered_amount:,.0f}")
    col3.metric("完成率", f"{delivered_amount/task_amount*100:.1f}%" if task_amount > 0 else "0%")
    
    if st.session_state.salesperson_view == "preview":
        st.divider()
        st.subheader("产品列表")
        
        if not products:
            st.info("暂无产品")
        else:
            header_cols = st.columns([1, 2, 2, 1, 1])
            with header_cols[0]:
                st.markdown("**状态**")
            with header_cols[1]:
                st.markdown("**Name**")
            with header_cols[2]:
                st.markdown("**类型**")
            with header_cols[3]:
                st.markdown("**等级**")
            with header_cols[4]:
                st.markdown("**操作**")
            
            st.markdown("---")
            
            for prod in products:
                row_cols = st.columns([1, 2, 2, 1, 1])
                with row_cols[0]:
                    status_icon = "✓" if prod.is_delivered else "○"
                    st.write(status_icon)
                with row_cols[1]:
                    st.write(prod.name)
                with row_cols[2]:
                    st.write(prod.product_type or "")
                with row_cols[3]:
                    st.write(prod.grade or "")
                with row_cols[4]:
                    if st.button("切换", key=f"toggle_{prod.id}"):
                        prod.is_delivered = not prod.is_delivered
                        db.commit()
                        st.rerun()
    
    elif st.session_state.salesperson_view == "edit":
        with st.expander("⚙️ 参数配置", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                new_c = st.number_input(f"参数C (默认{PARAM_C})", value=float(PARAM_C), min_value=0.0, step=10.0)
            with col2:
                new_d = st.number_input(f"参数D (默认{PARAM_D})", value=float(PARAM_D), min_value=0.0, step=10.0)
            
            if st.button("保存参数"):
                config.param_c = new_c
                config.param_d = new_d
                db.commit()
                st.success("参数已保存")
                st.rerun()
            
            st.info(f"产品金额 = 参数A - {new_c + new_d}")
        
        st.divider()
        st.subheader("➕ 新增产品")
        
        with st.form("add_product_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                prod_name = st.text_input("产品名字*", key="prod_name")
            with col2:
                prod_years = st.text_input("年限", key="prod_years")
            with col3:
                prod_type = st.text_input("类型", key="prod_type")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("等级")
                g1 = st.checkbox("1级", key="grade_1")
                g2 = st.checkbox("2级", key="grade_2")
                g3 = st.checkbox("3级", key="grade_3")
                g4 = st.checkbox("4级", key="grade_4")
                grades = []
                if g1: grades.append("1级")
                if g2: grades.append("2级")
                if g3: grades.append("3级")
                if g4: grades.append("4级")
                grade_str = "/".join(grades)
            with col2:
                prod_param_a = st.number_input("参数A*", min_value=1.0, step=100.0, key="prod_param_a")
            
            prod_amount = prod_param_a - FORMULA_AMOUNT if prod_param_a > 0 else 0
            st.write(f"计算金额: ¥{prod_amount:,.0f}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                prod_date = st.date_input("生产日期", value=date.today(), key="prod_date")
            with col2:
                prod_expire = st.date_input("过期时间", value=date.today() + timedelta(days=365), key="prod_expire")
            with col3:
                prod_seal = st.date_input("盖章日期", value=date.today(), key="prod_seal")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                prod_seal_expire = st.date_input("盖章过期时间", value=date.today() + timedelta(days=365), key="prod_seal_expire")
            with col2:
                prod_contact = st.text_input("联系方式", key="prod_contact")
            with col3:
                prod_emergency = st.text_input("紧急联系", key="prod_emergency")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                prod_address = st.text_area("地址", key="prod_address")
            with col2:
                prod_remark = st.text_area("备注", key="prod_remark")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("录入产品", use_container_width=True)
            with col2:
                if st.form_submit_button("清空", use_container_width=True):
                    st.rerun()
        
        if submitted:
            if prod_name and prod_param_a:
                if check_duplicate_product(person.id, prod_name):
                    st.error(f"产品「{prod_name}」已存在！不能重复添加。")
                else:
                    product = Product(
                        salesperson_id=person.id,
                        name=prod_name,
                        years=prod_years,
                        product_type=prod_type,
                        grade=grade_str,
                        param_a=prod_param_a,
                        production_date=prod_date,
                        expire_date=prod_expire,
                        seal_date=prod_seal,
                        seal_expire_date=prod_seal_expire,
                        contact=prod_contact,
                        address=prod_address,
                        emergency_contact=prod_emergency,
                        remark=prod_remark,
                        is_approved=True,
                        is_delivered=False,
                        created_date=date.today()
                    )
                    db.add(product)
                    db.commit()
                    recalculate_target_amounts()
                    st.success("录入成功")
                    st.rerun()
            else:
                st.error("请填写必填项*")
        
        st.divider()
        st.subheader("📥 批量导入")
        
        uploaded_file = st.file_uploader("上传Excel文件", type=["xlsx"], key="import_file")
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.dataframe(df.head(10))
                
                if st.button("确认导入到当前销售员"):
                    imported_count = 0
                    for _, row in df.iterrows():
                        if pd.isna(row.get("产品名字")):
                            continue
                        product = Product(
                            salesperson_id=person.id,
                            name=row.get("产品名字", ""),
                            years=str(row.get("年限", "")) if pd.notna(row.get("年限")) else "",
                            product_type=str(row.get("类型", "")) if pd.notna(row.get("类型")) else "",
                            grade=str(row.get("等级", "")) if pd.notna(row.get("等级")) else "",
                            param_a=float(row.get("参数A", 0)) if pd.notna(row.get("参数A")) else 0,
                            production_date=row.get("生产日期") if pd.notna(row.get("生产日期")) else None,
                            expire_date=row.get("过期时间") if pd.notna(row.get("过期时间")) else None,
                            seal_date=row.get("盖章日期") if pd.notna(row.get("盖章日期")) else None,
                            seal_expire_date=row.get("盖章过期时间") if pd.notna(row.get("盖章过期时间")) else None,
                            contact=str(row.get("联系方式", "")) if pd.notna(row.get("联系方式")) else "",
                            address=str(row.get("地址", "")) if pd.notna(row.get("地址")) else "",
                            emergency_contact=str(row.get("紧急联系", "")) if pd.notna(row.get("紧急联系")) else "",
                            remark=str(row.get("备注", "")) if pd.notna(row.get("备注")) else "",
                            is_approved=True,
                            is_delivered=False,
                            created_date=date.today()
                        )
                        db.add(product)
                        imported_count += 1
                    db.commit()
                    recalculate_target_amounts()
                    st.success(f"成功导入 {imported_count} 条产品数据")
                    st.rerun()
            except Exception as e:
                st.error(f"导入失败: {e}")
        
        st.divider()
        st.subheader("产品列表")
        
        if not products:
            st.info("暂无产品")
        else:
            for prod in products:
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
                    with col1:
                        status_icon = "✓" if prod.is_delivered else "○"
                        st.write(status_icon)
                    with col2:
                        st.write(f"**{prod.name}**")
                    with col3:
                        st.write(f"{prod.product_type or ''} {prod.grade or ''}")
                    with col4:
                        if st.button("删除", key=f"del_{prod.id}"):
                            st.session_state[f"confirm_delete_{prod.id}"] = True
                
                if st.session_state.get(f"confirm_delete_{prod.id}", False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.warning(f"确认删除「{prod.name}」？")
                    with col2:
                        if st.button("确定删除", key=f"confirm_{prod.id}"):
                            db.delete(prod)
                            db.commit()
                            recalculate_target_amounts()
                            st.success("已删除")
                            st.rerun()
                        if st.button("取消", key=f"cancel_{prod.id}"):
                            st.session_state[f"confirm_delete_{prod.id}"] = False
                            st.rerun()
                
                st.divider()

elif st.session_state.current_page == "export":
    st.title("📥 导出数据")
    
    if st.button("← 返回首页"):
        navigate("home")
        st.rerun()
    
    st.divider()
    st.subheader("筛选条件")
    
    persons = db.query(SalesPerson).all()
    person_options = ["全部"] + [p.name for p in persons]
    selected_person = st.selectbox("选择销售员", person_options)
    
    st.divider()
    st.subheader("选择导出字段")
    
    export_cols = ["销售员"] + ALL_COLUMNS
    selected_cols = []
    cols_per_row = 4
    
    for row_start in range(0, len(export_cols), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = row_start + j
            if idx >= len(export_cols):
                break
            col = export_cols[idx]
            default_checked = col in DEFAULT_COLUMNS or col == "销售员"
            with cols[j]:
                checked = st.checkbox(col, value=default_checked, key=f"export_col_{idx}")
                if checked:
                    selected_cols.append(col)
    
    st.divider()
    st.subheader("数据预览")
    
    if selected_person == "全部":
        filter_products = db.query(Product).all()
    else:
        person = db.query(SalesPerson).filter(SalesPerson.name == selected_person).first()
        filter_products = db.query(Product).filter(Product.salesperson_id == person.id).all() if person else []
    
    if selected_cols and filter_products:
        data = []
        for prod in filter_products:
            person = db.query(SalesPerson).filter(SalesPerson.id == prod.salesperson_id).first()
            row = {}
            for col in selected_cols:
                if col == "销售员":
                    row[col] = person.name
                elif col == "产品名字":
                    row[col] = prod.name
                elif col == "年限":
                    row[col] = prod.years or ""
                elif col == "类型":
                    row[col] = prod.product_type or ""
                elif col == "等级":
                    row[col] = prod.grade or ""
                elif col == "参数A":
                    row[col] = prod.param_a
                elif col == "生产日期":
                    row[col] = str(prod.production_date) if prod.production_date else ""
                elif col == "过期时间":
                    row[col] = str(prod.expire_date) if prod.expire_date else ""
                elif col == "盖章日期":
                    row[col] = str(prod.seal_date) if prod.seal_date else ""
                elif col == "盖章过期时间":
                    row[col] = str(prod.seal_expire_date) if prod.seal_expire_date else ""
                elif col == "联系方式":
                    row[col] = prod.contact or ""
                elif col == "地址":
                    row[col] = prod.address or ""
                elif col == "紧急联系":
                    row[col] = prod.emergency_contact or ""
                elif col == "备注":
                    row[col] = prod.remark or ""
            data.append(row)
        
        df = pd.DataFrame(data)
        st.dataframe(df, hide_index=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        
        st.download_button(
            label="📥 下载Excel",
            data=buffer,
            file_name="sales_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("请选择销售员并勾选导出字段")
    
    st.divider()
    st.subheader("下载导入模板")
    
    template_cols = ["销售员"] + ALL_COLUMNS
    template_df = pd.DataFrame(columns=template_cols)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        template_df.to_excel(writer, index=False)
    buffer.seek(0)
    
    st.download_button(
        label="📥 下载模板",
        data=buffer,
        file_name="import_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

db.close()
