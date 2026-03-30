# 记账核算工具

分销模式销售记账核算工具

## 技术栈
- Streamlit (桌面应用)
- SQLite (本地数据库)
- 后续: FastAPI + Vue (云端)

## 功能
- 首页 Dashboard：统计概览 + 销售员卡片
- 详情页：产品列表 + 点击切换交付状态
- 参数配置：参数A 管理与审批流程
- 数据导入/导出 Excel

## 快速启动
```bash
cd backend
pip install -r requirements.txt
streamlit run app.py
```

## 数据初始化
```bash
python init_data.py
```
