import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import engine, Base, SessionLocal
from models import SalesPerson, Product, SystemConfig
import io

st.set_page_config(page_title="记账核算工具", layout="wide")

st.markdown("""
<style>
    /* 全局样式 */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* 主标题 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a1a2e;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* 统计卡片 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .metric-card-green {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        box-shadow: 0 4px 15px rgba(17, 153, 142, 0.3);
    }
    
    .metric-card-orange {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        box-shadow: 0 4px 15px rgba(245, 87, 108, 0.3);
    }
    
    /* 销售员卡片 */
    .person-card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
        height: 100%;
    }
    
    .person-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    .person-name {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.5rem;
    }
    
    .person-stat {
        color: #6b7280;
        font-size: 0.95rem;
        margin: 0.3rem 0;
    }
    
    .progress-bar {
        background: #e5e7eb;
        border-radius: 10px;
        height: 8px;
        margin-top: 0.8rem;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transition: width 0.3s ease;
    }
    
    .progress-fill-green {
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
    }
    
    /* 按钮样式 */
    .stButton > button {
        border-radius: 12px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        border: none;
        transition: all 0.2s;
    }
    
    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .btn-secondary {
        background: #e5e7eb;
        color: #4b5563;
    }
    
    /* 产品卡片 */
    .product-card {
        background: white;
        border-radius: 16px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .product-info {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .status-icon {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }
    
    .status-pending {
        background: #fef3c7;
        color: #f59e0b;
    }
    
    .status-delivered {
        background: #d1fae5;
        color: #10b981;
    }
    
    .product-name {
        font-weight: 600;
        color: #1a1a2e;
    }
    
    .product-type {
        font-size: 0.85rem;
        color: #6b7280;
    }
    
    .product-amount {
        font-weight: 600;
        color: #667eea;
    }
    
    /* 分隔线 */
    .custom-divider {
        margin: 1.5rem 0;
        border: none;
        border-top: 1px solid #e5e7eb;
    }
    
    /* 头部按钮组 */
    .header-btn {
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 12px;
        padding: 0.8rem 1.5rem;
        font-weight: 500;
        color: #4b5563;
        transition: all 0.2s;
    }
    
    .header-btn:hover {
        border-color: #667eea;
        color: #667eea;
    }
    
    .header-btn-active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
    }
    
    /* 标签页 */
    .nav-tab {
        background: white;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
    }
    
    /* 可点击卡片 */
    .clickable-card {
        cursor: pointer;
    }
    
    .clickable-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
</style>
""", unsafe_allow_html=True)

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

def render_progress_bar(delivered, total, height=8):
    if total == 0:
        pct = 0
    else:
        pct = delivered / total * 100
    return f"""
    <div class="progress-bar" style="height: {height}px;">
        <div class="progress-fill" style="width: {pct}%;"></div>
    </div>
    <div style="display: flex; justify-content: space-between; margin-top: 0.3rem; font-size: 0.85rem; color: #6b7280;">
        <span>{delivered}/{total}</span>
        <span>{pct:.0f}%</span>
    </div>
    """

if st.session_state.current_page == "home":
    st.markdown('<h1 class="main-title">📊 分销记账核算工具</h1>', unsafe_allow_html=True)
    
    total_persons = db.query(SalesPerson).count()
    all_persons = db.query(SalesPerson).all()
    total_target = sum(p.target_amount for p in all_persons)
    
    all_products = db.query(Product).all()
    total_delivered_amount = sum(p.amount for p in all_products if p.is_delivered)
    total_delivered_count = sum(1 for p in all_products if p.is_delivered)
    total_product_count = len(all_products)
    
    pending_approvals = db.query(Product).filter(Product.is_approved == False).count()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="height: 100%;">
            <div style="font-size: 2rem; font-weight: 700;">{total_persons}</div>
            <div style="opacity: 0.9;">销售员人数</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card metric-card-green" style="height: 100%;">
            <div style="font-size: 1.5rem; font-weight: 700;">¥{total_target:,.0f}</div>
            <div style="font-size: 1rem; opacity: 0.9;">目标总金额</div>
            <div style="margin-top: 0.5rem; font-size: 1.5rem; font-weight: 700;">¥{total_delivered_amount:,.0f}</div>
            <div style="font-size: 1rem; opacity: 0.9;">已完成金额</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="height: 100%;">
            <div style="font-size: 2rem; font-weight: 700;">{total_delivered_count}/{total_product_count}</div>
            <div style="opacity: 0.9;">完成总数量</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card metric-card-orange" style="height: 100%;">
            <div style="font-size: 2rem; font-weight: 700;">{pending_approvals}</div>
            <div style="opacity: 0.9;">待审批</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("➕ 新增销售员", use_container_width=True):
            navigate("add_salesperson")
    with col_btn2:
        if st.button("👥 销售员管理", use_container_width=True):
            navigate("manage_salesperson")
    with col_btn3:
        if st.button("📥 导出数据", use_container_width=True):
            navigate("export")
    
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    st.subheader("👥 销售员列表")
    
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
            total_count = len(products)
            
            with cols[idx % 3]:
                card_content = f"""👤 {person.name}
────────────────────
任务金额: ¥{task_amount:,.0f}
任务数量: {delivered_count}/{total_count}
────────────────────
👆 点击进入详情"""
                if st.button(card_content, key=f"btn_{person.id}", use_container_width=True):
                    go_salesperson(person.id)
            
            st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

elif st.session_state.current_page == "add_salesperson":
    st.title("➕ 新增销售员")
    
    if st.button("← 返回首页"):
        navigate("home")
        st.rerun()
    
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    
    with st.expander("⚙️ 参数配置 (参数C/D)", expanded=False):
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
    
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    st.subheader("新增销售员")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        new_name = st.text_input("销售员姓名")
    with col2:
        st.write("")  # 占位
    
    if st.button("添加", use_container_width=True):
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
    
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    st.subheader("已有销售员")
    
    persons = db.query(SalesPerson).all()
    for p in persons:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"👤 **{p.name}**")
        with col2:
            st.write(f"任务: ¥{p.target_amount:,.0f}")
        with col3:
            if st.button("进入", key=f"enter_{p.id}"):
                go_salesperson(p.id)
    
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    st.subheader("参数A 审批管理")
    
    pending_products = db.query(Product).filter(Product.is_approved == False).all()
    
    if not pending_products:
        st.success("✓ 暂无待审批项目")
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

elif st.session_state.current_page == "manage_salesperson":
    st.title("👥 销售员管理")
    
    if st.button("← 返回首页"):
        navigate("home")
        st.rerun()
    
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    
    persons = db.query(SalesPerson).all()
    
    if not persons:
        st.info("暂无销售员数据")
    else:
        header_cols = st.columns([2, 2, 3, 3, 2, 2, 1])
        with header_cols[0]:
            st.markdown("**销售员**")
        with header_cols[1]:
            st.markdown("**产品数量**")
        with header_cols[2]:
            st.markdown("**建立时间**")
        with header_cols[3]:
            st.markdown("**合作时间**")
        with header_cols[4]:
            st.markdown("**详情**")
        with header_cols[5]:
            st.markdown("**删除**")
        with header_cols[6]:
            st.markdown("**操作**")
        
        st.markdown("---")
        
        for person in persons:
            products = db.query(Product).filter(Product.salesperson_id == person.id).all()
            product_count = len(products)
            
            created_date = products[0].created_date if products else date.today()
            days_since_creation = (date.today() - created_date).days if created_date else 0
            
            col_vals = st.columns([2, 2, 3, 3, 2, 2, 1])
            with col_vals[0]:
                st.write(f"👤 {person.name}")
            with col_vals[1]:
                st.write(str(product_count))
            with col_vals[2]:
                st.write(str(created_date))
            with col_vals[3]:
                st.write(f"{days_since_creation} 天")
            with col_vals[4]:
                if st.button("详情", key=f"detail_{person.id}"):
                    go_salesperson(person.id)
            with col_vals[5]:
                if st.button("删除", key=f"delete_btn_{person.id}"):
                    st.session_state[f"show_delete_confirm_{person.id}"] = True
            
            if st.session_state.get(f"show_delete_confirm_{person.id}", False):
                st.markdown("""
                <div style="background: #fef3cd; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                    <b>⚠️ 确认删除「{}」？</b><br>
                    此操作将同时删除该销售员下的 {} 个产品<br>
                    <b>请提前备份数据！</b>
                </div>
                """.format(person.name, product_count), unsafe_allow_html=True)
                
                col_confirm = st.columns(2)
                with col_confirm[0]:
                    if st.button("确认删除", key=f"do_delete_{person.id}"):
                        db.query(Product).filter(Product.salesperson_id == person.id).delete()
                        db.delete(person)
                        db.commit()
                        recalculate_target_amounts()
                        st.success("已删除")
                        st.rerun()
                with col_confirm[1]:
                    if st.button("取消", key=f"cancel_delete_{person.id}"):
                        st.session_state[f"show_delete_confirm_{person.id}"] = False
                        st.rerun()
            
            st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

elif st.session_state.current_page == "salesperson":
    person = db.query(SalesPerson).filter(SalesPerson.id == st.session_state.selected_person_id).first()
    
    if "salesperson_view" not in st.session_state:
        st.session_state.salesperson_view = "preview"
    
    products = db.query(Product).filter(Product.salesperson_id == person.id).all()
    delivered_amount = sum(p.amount for p in products if p.is_delivered)
    task_amount = sum(p.amount for p in products)
    delivered_count = sum(1 for p in products if p.is_delivered)
    
    col_header1, col_header2, col_header3 = st.columns([1, 1, 1])
    with col_header1:
        if st.button("← 返回首页"):
            navigate("home")
            st.rerun()
    with col_header2:
        if st.button("📋 预览", use_container_width=True):
            st.session_state.salesperson_view = "preview"
            st.rerun()
    with col_header3:
        if st.button("✏️ 编辑", use_container_width=True):
            st.session_state.salesperson_view = "edit"
            st.rerun()
    
    st.markdown(f'<h2 class="main-title">👤 {person.name}</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="height: 100%;">
            <div style="font-size: 1.3rem; font-weight: 700;">¥{task_amount:,.0f} / ¥{delivered_amount:,.0f}</div>
            <div style="opacity: 0.9;">任务金额 / 完成金额</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        total_count = len(products)
        st.markdown(f"""
        <div class="metric-card metric-card-green" style="height: 100%;">
            <div style="font-size: 1.5rem; font-weight: 700;">{delivered_count}/{total_count}</div>
            <div style="opacity: 0.9;">完成数量</div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.salesperson_view == "preview":
        st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
        st.subheader("📋 产品列表")
        
        if not products:
            st.info("暂无产品")
        else:
            header_cols = st.columns([1, 1, 2, 2, 2, 2, 1])
            with header_cols[0]:
                st.markdown("**序号**")
            with header_cols[1]:
                st.markdown("**状态**")
            with header_cols[2]:
                st.markdown("**Name**")
            with header_cols[3]:
                st.markdown("**类型**")
            with header_cols[4]:
                st.markdown("**等级**")
            with header_cols[5]:
                st.markdown("**参数A**")
            with header_cols[6]:
                st.markdown("**操作**")
            
            st.markdown("---")
            
            for idx, prod in enumerate(products, 1):
                row_cols = st.columns([1, 1, 2, 2, 2, 2, 1])
                with row_cols[0]:
                    st.write(str(idx))
                with row_cols[1]:
                    if prod.is_delivered:
                        st.markdown("<div class='status-icon status-delivered'>✓</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='status-icon status-pending'>○</div>", unsafe_allow_html=True)
                with row_cols[2]:
                    st.markdown(f"<div class='product-name'>{prod.name}</div>", unsafe_allow_html=True)
                with row_cols[3]:
                    st.write(prod.product_type or "-")
                with row_cols[4]:
                    st.write(prod.grade or "-")
                with row_cols[5]:
                    st.write(f"¥{prod.param_a:,.0f}")
                with row_cols[6]:
                    if st.button("切换", key=f"toggle_{prod.id}"):
                        prod.is_delivered = not prod.is_delivered
                        db.commit()
                        st.rerun()
    
    elif st.session_state.salesperson_view == "edit":
        with st.expander("⚙️ 参数配置", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                new_c = st.number_input(f"参数C", value=float(PARAM_C), min_value=0.0, step=10.0)
            with col2:
                new_d = st.number_input(f"参数D", value=float(PARAM_D), min_value=0.0, step=10.0)
            
            if st.button("保存参数"):
                config.param_c = new_c
                config.param_d = new_d
                db.commit()
                st.success("参数已保存")
                st.rerun()
        
        st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
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
                grade_str = st.selectbox("等级", ["", "1级", "2级", "3级", "4级"], key="grade_select")
            with col2:
                prod_param_a = st.number_input("参数A*", min_value=0.0, step=100.0, key="prod_param_a")
            
            prod_amount = prod_param_a - FORMULA_AMOUNT if prod_param_a > 0 else 0
            st.info(f"计算金额: ¥{prod_amount:,.0f}")
            
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
        
        st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
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
        
        st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
        st.subheader("产品列表")
        
        if not products:
            st.info("暂无产品")
        else:
            for prod in products:
                edit_key = f"edit_mode_{prod.id}"
                
                if st.session_state.get(edit_key, False):
                    with st.expander(f"✏️ 编辑: {prod.name}", expanded=True):
                        with st.form(f"edit_form_{prod.id}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                edit_name = st.text_input("产品名字*", value=prod.name, key=f"edit_name_{prod.id}")
                            with col2:
                                edit_years = st.text_input("年限", value=prod.years or "", key=f"edit_years_{prod.id}")
                            with col3:
                                edit_type = st.text_input("类型", value=prod.product_type or "", key=f"edit_type_{prod.id}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                edit_grade = st.selectbox("等级", ["", "1级", "2级", "3级", "4级"], index=["", "1级", "2级", "3级", "4级"].index(prod.grade or "") if (prod.grade or "") in ["", "1级", "2级", "3级", "4级"] else 0, key=f"edit_grade_{prod.id}")
                            with col2:
                                edit_param_a = st.number_input("参数A*", value=prod.param_a, min_value=0.0, step=100.0, key=f"edit_param_a_{prod.id}")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                edit_date = st.date_input("生产日期", value=prod.production_date or date.today(), key=f"edit_date_{prod.id}")
                            with col2:
                                edit_expire = st.date_input("过期时间", value=prod.expire_date or date.today() + timedelta(days=365), key=f"edit_expire_{prod.id}")
                            with col3:
                                edit_seal = st.date_input("盖章日期", value=prod.seal_date or date.today(), key=f"edit_seal_{prod.id}")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                edit_seal_expire = st.date_input("盖章过期时间", value=prod.seal_expire_date or date.today() + timedelta(days=365), key=f"edit_seal_expire_{prod.id}")
                            with col2:
                                edit_contact = st.text_input("联系方式", value=prod.contact or "", key=f"edit_contact_{prod.id}")
                            with col3:
                                edit_emergency = st.text_input("紧急联系", value=prod.emergency_contact or "", key=f"edit_emergency_{prod.id}")
                            
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                edit_address = st.text_area("地址", value=prod.address or "", key=f"edit_address_{prod.id}")
                            with col2:
                                edit_remark = st.text_area("备注", value=prod.remark or "", key=f"edit_remark_{prod.id}")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                submitted = st.form_submit_button("保存修改", use_container_width=True)
                            with col2:
                                canceled = st.form_submit_button("取消", use_container_width=True)
                            with col3:
                                deleted = st.form_submit_button("删除产品", use_container_width=True)
                            
                            if submitted:
                                prod.name = edit_name
                                prod.years = edit_years
                                prod.product_type = edit_type
                                prod.grade = edit_grade
                                prod.param_a = edit_param_a
                                prod.production_date = edit_date
                                prod.expire_date = edit_expire
                                prod.seal_date = edit_seal
                                prod.seal_expire_date = edit_seal_expire
                                prod.contact = edit_contact
                                prod.emergency_contact = edit_emergency
                                prod.address = edit_address
                                prod.remark = edit_remark
                                db.commit()
                                recalculate_target_amounts()
                                st.success("已保存")
                                st.rerun()
                            
                            if canceled:
                                st.session_state[edit_key] = False
                                st.rerun()
                            
                            if deleted:
                                db.delete(prod)
                                db.commit()
                                recalculate_target_amounts()
                                st.success("已删除")
                                st.rerun()
                else:
                    col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 2, 2, 1])
                    with col1:
                        if prod.is_delivered:
                            st.markdown("<div class='status-icon status-delivered'>✓</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div class='status-icon status-pending'>○</div>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"<div class='product-name'>{prod.name}</div>", unsafe_allow_html=True)
                    with col3:
                        st.write(prod.product_type or "-")
                    with col4:
                        st.write(prod.grade or "-")
                    with col5:
                        st.write(f"¥{prod.param_a:,.0f}")
                    with col6:
                        if st.button("编辑", key=f"edit_{prod.id}"):
                            st.session_state[edit_key] = True
                            st.rerun()
                        if st.button("删除", key=f"del_{prod.id}"):
                            st.session_state[f"confirm_delete_{prod.id}"] = True
                            st.rerun()
                
                if st.session_state.get(f"confirm_delete_{prod.id}", False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.warning(f"确认删除「{prod.name}」？")
                    with col2:
                        if st.button("确定", key=f"confirm_{prod.id}"):
                            db.delete(prod)
                            db.commit()
                            recalculate_target_amounts()
                            st.success("已删除")
                            st.rerun()
                        if st.button("取消", key=f"cancel_{prod.id}"):
                            st.session_state[f"confirm_delete_{prod.id}"] = False
                            st.rerun()
                
                st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

elif st.session_state.current_page == "export":
    st.title("📥 导出数据")
    
    if st.button("← 返回首页"):
        navigate("home")
        st.rerun()
    
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    st.subheader("筛选条件")
    
    persons = db.query(SalesPerson).all()
    person_options = ["全部"] + [p.name for p in persons]
    selected_person = st.selectbox("选择销售员", person_options)
    
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
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
    
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
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
    
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
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
