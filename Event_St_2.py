import streamlit as st
import pandas as pd
import os
import hashlib
import uuid

# -----------------------------
# 配置区（同前）
# -----------------------------

participants = [
    {"编号": 1, "姓名": "张罡铭"}, {"编号": 2, "姓名": "王小波"}, {"编号": 3, "姓名": "胡梅"},
    {"编号": 4, "姓名": "陈宇"}, {"编号": 5, "姓名": "谌淼"}, {"编号": 6, "姓名": "杨强"},
    {"编号": 7, "姓名": "古棋元"}, {"编号": 8, "姓名": "陈鑫"}, {"编号": 9, "姓名": "朱虹润"},
    {"编号": 10, "姓名": "文钰"}, {"编号": 11, "姓名": "李俊橙"}, {"编号": 12, "姓名": "董余"},
    {"编号": 13, "姓名": "付勇"}, {"编号": 14, "姓名": "胡佳佳"}, {"编号": 15, "姓名": "黄荆荣"},
    {"编号": 16, "姓名": "李治兴"},
]

weights = {
    "内容契合度": 25,
    "语言表达": 20,
    "情感表现": 20,
    "朗诵技巧": 15,
    "台风形象": 10,
    "原创/创意": 10,
}

MAX_TOTAL = sum(weights.values())
SCORES_FILE = "scores.csv"
PUBLISHER_PASSWORD = "admin123"  # ← 修改为你的密码

# -----------------------------
# 工具函数
# -----------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_scores():
    if os.path.exists(SCORES_FILE):
        df = pd.read_csv(SCORES_FILE)
        if "device_id" not in df.columns:
            df["device_id"] = ""
        return df
    else:
        return pd.DataFrame(
            columns=["评委ID", "device_id", "编号", "姓名"] + list(weights.keys()) + ["总分"]
        )

def save_scores(df):
    df.to_csv(SCORES_FILE, index=False)

def clear_scores():
    if os.path.exists(SCORES_FILE):
        os.remove(SCORES_FILE)

# ✅ 改进的设备ID生成：使用 session_id + IP + User-Agent 混合
def get_device_id():
    # 尝试获取真实IP
    try:
        xff = st.context.request.headers.get("X-Forwarded-For", "")
        ip = xff.split(",")[0].strip() if xff else "127.0.0.1"
    except:
        ip = "127.0.0.1"

    try:
        ua = st.context.request.headers.get("User-Agent", "")
    except:
        ua = ""

    # 使用 Streamlit 的 session_id（每个浏览器唯一）
    try:
        session_id = st.session_state.get("session_id", str(uuid.uuid4()))
        if "session_id" not in st.session_state:
            st.session_state.session_id = session_id
    except:
        session_id = str(uuid.uuid4())

    # 混合生成设备指纹
    device_str = f"{session_id}-{ip}-{ua}"
    return hashlib.md5(device_str.encode()).hexdigest()

# ✅ 检查设备是否已提交
def has_submitted(device_id):
    if not device_id or not os.path.exists(SCORES_FILE):
        return False
    df = load_scores()
    if "device_id" not in df.columns:
        return False
    submitted_ids = df["device_id"].dropna().astype(str).str.strip()
    return device_id in submitted_ids.values

# -----------------------------
# 初始化状态
# -----------------------------

# ✅ 每个浏览器会话生成唯一 device_id
if "device_id" not in st.session_state:
    st.session_state.device_id = get_device_id()

device_id = st.session_state.device_id

# 检查是否已提交
if "has_submitted" not in st.session_state:
    st.session_state.has_submitted = has_submitted(device_id)

# 评委ID
if "judge_id" not in st.session_state:
    all_scores = load_scores()
    judge_count = len(all_scores["评委ID"].dropna().unique()) if "评委ID" in all_scores.columns else 0
    st.session_state.judge_id = f"J{judge_count + 1:03d}"

all_scores = load_scores()

# -----------------------------
# 页面主函数
# -----------------------------

def main():
    st.title("🎙️ 技术党支部朗诵活动打分表（匿名在线评分）")

    # ✅ 重新检查是否已提交（防止 session_state 和文件不一致）
    if "has_submitted" in st.session_state and not st.session_state.has_submitted:
        # 再次校验
        if has_submitted(device_id):
            st.session_state.has_submitted = True

    # 显示提交提示
    if st.session_state.has_submitted:
        st.success("✅ 感谢您的评分！您已成功提交，每个设备仅可提交一次。")
    else:
        show_scoring_form()

    # ========== 发布者管理 ==========
    st.sidebar.title("🔐 发布者管理")
    pwd = st.sidebar.text_input("请输入发布者密码", type="password")
    
    if st.sidebar.button("登录"):
        if hash_password(pwd) == hash_password(PUBLISHER_PASSWORD):
            st.session_state.publisher_logged_in = True
            st.sidebar.success("登录成功！")
        else:
            st.sidebar.error("密码错误")

    if st.session_state.get("publisher_logged_in", False):
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 管理功能")

        valid_scores = all_scores[all_scores["device_id"].notna() & (all_scores["device_id"] != "")]
        submitted_count = valid_scores["device_id"].nunique()

        st.sidebar.write(f"✅ 已收到 {submitted_count} 份评分")
        st.sidebar.write(f"🎯 共 {len(participants)} 位参赛者")

        if st.sidebar.button("🗑️ 一键清除所有评分"):
            clear_scores()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.cache_data.clear()
            st.sidebar.success("✅ 所有评分已清除")
            st.rerun()

        display_final_scores_publisher()

# -----------------------------
# 打分表单
# -----------------------------

def show_scoring_form():
    st.subheader("📝 请为每位参赛者打分（满分100分）")
    st.markdown("📌 **评分标准**：")
    for category, max_score in weights.items():
        st.markdown(f"- **{category}**：满分 {max_score} 分")

    new_scores = []
    with st.form("scoring_form"):
        for participant in participants:
            with st.expander(f"🎤 {participant['姓名']} (编号: {participant['编号']})", True):
                score_row = {
                    "评委ID": st.session_state.judge_id,
                    "device_id": device_id,
                    "编号": participant["编号"],
                    "姓名": participant["姓名"],
                }
                total = 0
                cols = st.columns(len(weights))
                for i, (category, max_score) in enumerate(weights.items()):
                    with cols[i]:
                        score = st.number_input(
                            f"{category} (0~{max_score})",
                            0, max_score, step=1,
                            key=f"{participant['编号']}_{category}"
                        )
                        score_row[category] = score
                        total += score
                score_row["总分"] = total
                new_scores.append(score_row)

        if st.form_submit_button("📤 提交评分"):
            # 校验
            for row in new_scores:
                for cat, max_score in weights.items():
                    if not 0 <= row[cat] <= max_score:
                        st.error(f"❌ {cat} 超出范围")
                        return
            if has_submitted(device_id):
                st.error("⚠️ 已提交")
                st.session_state.has_submitted = True
                return

            # 保存
            new_df = pd.DataFrame(new_scores)
            global all_scores
            all_scores = pd.concat([all_scores, new_df], ignore_index=True)
            save_scores(all_scores)
            st.session_state.has_submitted = True
            st.success("🎉 提交成功！")

# -----------------------------
# 发布者查看结果
# -----------------------------

def display_final_scores_publisher():
    st.sidebar.subheader("📊 最终得分")
    valid = all_scores[all_scores["device_id"].notna() & (all_scores["device_id"] != "")]
    if valid.empty:
        st.sidebar.info("📭 暂无数据")
        return
    final = valid.groupby(["编号", "姓名"])["总分"].agg(
        平均分=("mean"), 评委人数=("count"), 最高分=("max"), 最低分=("min")
    ).round(2).reset_index()
    final = final.sort_values("平均分", ascending=False).reset_index(drop=True)
    final.insert(0, "排名", final.index + 1)
    st.sidebar.dataframe(final, use_container_width=True)
    st.sidebar.bar_chart(final.set_index("姓名")["平均分"])
    st.sidebar.download_button(
        "💾 导出数据",
        valid.to_csv(index=False),
        "评分数据.csv",
        "text/csv"
    )

# -----------------------------
# 启动
# -----------------------------

if __name__ == "__main__":
    main()
