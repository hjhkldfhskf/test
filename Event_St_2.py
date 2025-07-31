import streamlit as st
import pandas as pd
import qrcode
from PIL import Image
import uuid
import os
from datetime import datetime

# -----------------------------
# 配置与初始化
# -----------------------------

# 参赛者列表
participants = [
    {"编号": 1, "姓名": "张罡铭"},
    {"编号": 2, "姓名": "王小波"},
    {"编号": 3, "姓名": "胡梅"},
    {"编号": 4, "姓名": "陈宇"},
    {"编号": 5, "姓名": "谌淼"},
    {"编号": 6, "姓名": "杨强"},
    {"编号": 7, "姓名": "古棋元"},
    {"编号": 8, "姓名": "陈鑫"},
    {"编号": 9, "姓名": "朱虹润"},
    {"编号": 10, "姓名": "文钰"},
    {"编号": 11, "姓名": "李俊橙"},
    {"编号": 12, "姓名": "董余"},
    {"编号": 13, "姓名": "付勇"},
    {"编号": 14, "姓名": "胡佳佳"},
    {"编号": 15, "姓名": "黄荆荣"},
    {"编号": 16, "姓名": "李治兴"},
]

# 评分权重
weights = {
    "内容契合度": 25,
    "语言表达": 20,
    "情感表现": 20,
    "朗诵技巧": 15,
    "台风形象": 10,
    "原创/创意": 10,
}

# 创建必要目录
os.makedirs("qr_codes", exist_ok=True)

# 加载已有评分数据
if os.path.exists("scores.csv"):
    scores = pd.read_csv("scores.csv")
else:
    scores = pd.DataFrame(columns=["评委ID", "编号", "姓名"] + list(weights.keys()) + ["总分"])

# -----------------------------
# 页面主函数
# -----------------------------

def main():
    st.title("🎙️ 技术党支部朗诵活动打分表（匿名评分）")

    # 初始化匿名评委ID
    if "judge_id" not in st.session_state:
        st.session_state.judge_id = f"J{uuid.uuid4().hex[:6].upper()}"

    judge_id = st.session_state.judge_id

    # 生成二维码链接（带上 judge_id 参数）
    current_url = f"http://localhost:8501?judge_id={judge_id}"
    
    # 显示二维码
    st.subheader("📱 扫码开始打分")
    st.write("请使用微信扫描下方二维码，进入匿名打分页面。")
    generate_qr_code(judge_id, current_url)

    # 打分表单
    show_scoring_form(judge_id)

    # 显示当前评分汇总（可选：管理员查看）
    st.markdown("---")
    display_scores_summary()

# -----------------------------
# 生成二维码
# -----------------------------

def generate_qr_code(judge_id, url):
    img_path = f"qr_codes/{judge_id}.png"

    # 仅生成一次
    if not os.path.exists(img_path):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(img_path)

    # 显示二维码
    st.image(img_path, caption="微信扫码进入打分页面", use_container_width=True)

# -----------------------------
# 打分表单
# -----------------------------

def show_scoring_form(judge_id):
    global scores

    # 防止重复提交
    if f"submitted_{judge_id}" in st.session_state:
        st.info("✅ 您的评分已提交，不可重复提交。")
        return

    st.subheader("📝 请为每位参赛者打分")

    new_scores = []

    with st.form(key=f"scoring_form_{judge_id}"):
        for participant in participants:
            st.markdown(f"### 🎤 参赛者：{participant['姓名']} (编号: {participant['编号']})")

            score_row = {
                "评委ID": judge_id,  # 可选：用于防止重复，不展示给任何人
                "编号": participant["编号"],
                "姓名": participant["姓名"],
            }

            total = 0
            cols = st.columns(len(weights))
            for i, (category, max_score) in enumerate(weights.items()):
                with cols[i]:
                    score = st.slider(
                        f"{category}",
                        0, max_score,
                        key=f"{judge_id}_{participant['编号']}_{category}"
                    )
                    score_row[category] = score
                    total += score

            score_row["总分"] = total
            new_scores.append(score_row)

        submitted = st.form_submit_button("📤 提交评分")

        if submitted:
            new_df = pd.DataFrame(new_scores)
            global scores
            scores = pd.concat([scores, new_df], ignore_index=True)
            save_scores(scores)
            st.session_state[f"submitted_{judge_id}"] = True
            st.success("🎉 感谢您的评分！")

# -----------------------------
# 显示评分汇总（可选：仅管理员可见）
# -----------------------------

def display_scores_summary():
    st.subheader("📊 当前评分汇总（匿名）")
    if scores.empty:
        st.info("📭 暂无评分数据")
    else:
        # 展示时不显示评委ID（完全匿名）
        display_df = scores.drop(columns=["评委ID"], errors='ignore')
        st.dataframe(display_df, use_container_width=True)

# -----------------------------
# 保存评分数据
# -----------------------------

def save_scores(df):
    df.to_csv("scores.csv", index=False)

# -----------------------------
# 启动应用
# -----------------------------

if __name__ == "__main__":
    main()
