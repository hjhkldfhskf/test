import streamlit as st
import pandas as pd
import os
import hashlib
import uuid

# -----------------------------
# 配置区
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
PUBLISHER_PASSWORD = "admin123"  # ← 请修改为你的密码

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

# ✅ 生成设备唯一ID（基于 session + IP + User-Agent）
def get_device_id():
    # 获取 session_id（持久化在 session 中）
    if "device_fingerprint" not in st.session_state:
        st.session_state.device_fingerprint = str(uuid.uuid4())
    
    try:
        ip = st.context.request.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0].strip()
    except:
        ip = "127.0.0.1"
    
    try:
        ua = st.context.request.headers.get("User-Agent", "")
    except:
        ua = ""

    # 混合生成唯一指纹
    fingerprint = f"{st.session_state.device_fingerprint}-{ip}-{ua}"
    return hashlib.md5(fingerprint.encode()).hexdigest()

# ✅ 每次都从文件检查是否已提交（关键！）
def is_device_submitted(device_id):
    if not os.path.exists(SCORES_FILE):
        return False
    df = load_scores()
    if "device_id" not in df.columns:
        return False
    submitted_ids = df["device_id"].dropna().astype(str).str.strip()
    return device_id in submitted_ids.values

# -----------------------------
# 页面主函数
# -----------------------------

def main():
    st.title("🎙️ 技术党支部朗诵活动打分表（匿名在线评分）")

    # ✅ 每次加载都重新生成 device_id（但 session 中持久化 fingerprint）
    device_id = get_device_id()

    # ✅ 每次加载都从文件检查是否已提交（不依赖 session_state）
    has_submitted = is_device_submitted(device_id)

    # ✅ 如果已提交，直接显示提示，不再渲染表单
    if has_submitted:
        st.success("✅ 感谢您的评分！您已成功提交，每个设备仅可提交一次。")
        # 仍允许查看管理面板
        show_publisher_panel()
        return

    # ✅ 否则显示打分表单
    show_scoring_form(device_id)
    show_publisher_panel()

# -----------------------------
# 打分表单
# -----------------------------

def show_scoring_form(device_id):
    st.subheader("📝 请为每位参赛者打分（满分100分）")
    st.markdown("📌 **评分标准**：")
    for category, max_score in weights.items():
        st.markdown(f"- **{category}**：满分 {max_score} 分")

    # 生成唯一表单 key（避免缓存）
    form_key = f"scoring_form_{device_id[:8]}"

    new_scores = []
    with st.form(key=form_key):
        for participant in participants:
            with st.expander(f"🎤 {participant['姓名']} (编号: {participant['编号']})", expanded=True):
                score_row = {
                    "评委ID": f"J{len(load_scores()) + 1:03d}",
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
                            min_value=0,
                            max_value=max_score,
                            step=1,
                            key=f"{device_id}_{participant['编号']}_{category}"
                        )
                        score_row[category] = score
                        total += score
                score_row["总分"] = total
                new_scores.append(score_row)

        submitted = st.form_submit_button("📤 提交所有评分")

        if submitted:
            # 校验分数范围
            for row in new_scores:
                for category, max_score in weights.items():
                    if not (0 <= row[category] <= max_score):
                        st.error(f"❌ {category} 分数超出范围（0~{max_score}）")
                        return

            # ✅ 再次检查文件（防并发）
            if is_device_submitted(device_id):
                st.error("⚠️ 您的设备已提交过评分，不可重复提交。")
                return

            # 保存评分
            new_df = pd.DataFrame(new_scores)
            all_scores = load_scores()
            all_scores = pd.concat([all_scores, new_df], ignore_index=True)
            save_scores(all_scores)

            # ✅ 重新加载页面，确保下次进入时显示“已提交”
            st.success("🎉 感谢您的评分！数据已提交。")
            st.balloons()
            st.rerun()  # 重新加载，确保下次走 has_submitted 分支

# -----------------------------
# 发布者管理面板
# -----------------------------

def show_publisher_panel():
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

        all_scores = load_scores()
        if "device_id" in all_scores.columns:
            valid = all_scores[all_scores["device_id"].notna() & (all_scores["device_id"] != "")]
            count = valid["device_id"].nunique()
        else:
            count = 0

        st.sidebar.write(f"✅ 已收到 {count} 份评分")
        st.sidebar.write(f"🎯 共 {len(participants)} 位参赛者")

        if st.sidebar.button("🗑️ 一键清除所有评分"):
            clear_scores()
            st.session_state.clear()
            st.cache_data.clear()
            st.sidebar.success("✅ 所有评分已清除")
            st.rerun()

        display_final_scores_publisher()

# -----------------------------
# 发布者查看最终得分
# -----------------------------

def display_final_scores_publisher():
    st.sidebar.subheader("📊 最终得分（仅发布者可见）")
    all_scores = load_scores()
    if "device_id" in all_scores.columns:
        valid = all_scores[all_scores["device_id"].notna() & (all_scores["device_id"] != "")]
    else:
        valid = all_scores

    if valid.empty or valid["总分"].sum() == 0:
        st.sidebar.info("📭 暂无评分数据")
        return

    final = valid.groupby(["编号", "姓名"])["总分"].agg(
        平均分=("mean"),
        评委人数=("count"),
        最高分=("max"),
        最低分=("min")
    ).round(2).reset_index()

    final = final.sort_values(by="平均分", ascending=False).reset_index(drop=True)
    final.insert(0, "排名", final.index + 1)

    st.sidebar.dataframe(final, use_container_width=True)
    st.sidebar.bar_chart(final.set_index("姓名")["平均分"])

    csv = valid.to_csv(index=False)
    st.sidebar.download_button(
        "💾 导出原始评分数据",
        csv,
        "朗诵比赛评分数据.csv",
        "text/csv"
    )

# -----------------------------
# 启动应用
# -----------------------------

if __name__ == "__main__":
    main()
