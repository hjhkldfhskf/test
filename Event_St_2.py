import streamlit as st
import pandas as pd
import os
import hashlib

# -----------------------------
# 配置
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

# 总分满分
MAX_TOTAL = sum(weights.values())  # 100 分

# 评分数据文件
SCORES_FILE = "scores.csv"

# 发布者密码
PUBLISHER_PASSWORD = "admin123"  # ← 请修改

# -----------------------------
# 工具函数
# -----------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_scores():
    if os.path.exists(SCORES_FILE):
        df = pd.read_csv(SCORES_FILE)
        # ✅ 确保包含 device_id 列
        if "device_id" not in df.columns:
            df["device_id"] = ""  # 新增列，默认为空
        return df
    else:
        # ✅ 初始化时就包含 device_id
        return pd.DataFrame(
            columns=["评委ID", "device_id", "编号", "姓名"] 
            + list(weights.keys()) + ["总分"]
        )

def save_scores(df):
    df.to_csv(SCORES_FILE, index=False)

def clear_scores():
    if os.path.exists(SCORES_FILE):
        os.remove(SCORES_FILE)

# 获取设备指纹
def get_device_id():
    try:
        ip = st.context.request.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0].strip()
    except:
        ip = "127.0.0.1"

    try:
        user_agent = st.context.request.headers.get("User-Agent", "")
    except:
        user_agent = ""

    device_str = f"{ip}-{user_agent}"
    return hashlib.md5(device_str.encode()).hexdigest()

# 检查设备是否已提交
def has_submitted(device_id):
    if os.path.exists(SCORES_FILE):
        df = pd.read_csv(SCORES_FILE)
        if "device_id" not in df.columns:
            return False  # 如果没有该列，认为未提交
        return device_id in df["device_id"].dropna().values
    return False

# -----------------------------
# 初始化状态
# -----------------------------

# 获取设备ID
device_id = get_device_id()

# 检查是否已提交
if "has_submitted" not in st.session_state:
    st.session_state.has_submitted = has_submitted(device_id)

# 生成评委ID
if "judge_id" not in st.session_state:
    st.session_state.judge_id = f"J{len(load_scores()['评委ID'].unique()) + 1:03d}"

# 加载评分数据
all_scores = load_scores()  # ✅ 现在确保包含 device_id

# -----------------------------
# 页面主函数
# -----------------------------

def main():
    st.title("🎙️ 技术党支部朗诵活动打分表（匿名在线评分）")

    # ========== 显示打分状态（顶部提示）==========
    if st.session_state.has_submitted:
        st.success("✅ 感谢您的评分！您已成功提交，每个设备仅可提交一次。")

    # ========== 显示打分表单（仅未提交时）==========
    if not st.session_state.has_submitted:
        show_scoring_form()
    else:
        # ✅ 即使已提交，也继续显示管理面板
        pass  # 继续执行下面的管理功能

    # ========== 管理区：发布者登录 ==========
    st.sidebar.title("🔐 发布者管理")
    pwd = st.sidebar.text_input("请输入发布者密码", type="password")
    
    if st.sidebar.button("登录"):
        if hash_password(pwd) == hash_password(PUBLISHER_PASSWORD):
            st.session_state.publisher_logged_in = True
            st.sidebar.success("登录成功！")
        else:
            st.sidebar.error("密码错误")

    # ========== 发布者功能（仅登录后可见）==========
    if st.session_state.get("publisher_logged_in", False):
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 管理功能")

        # 安全获取已提交设备数
        if "device_id" in all_scores.columns:
            submitted_devices = all_scores[all_scores["device_id"] != ""]["device_id"].nunique()
        else:
            submitted_devices = 0

        st.sidebar.write(f"✅ 已收到 {submitted_devices} 份评分")
        st.sidebar.write(f"🎯 共 {len(participants)} 位参赛者")

        # 一键清除
        if st.sidebar.button("🗑️ 一键清除所有评分"):
            clear_scores()
            st.session_state.clear()
            st.cache_data.clear()
            st.sidebar.success("✅ 所有评分已清除，可重新开始")
            st.experimental_rerun()

        # 显示最终得分
        display_final_scores_publisher()

# -----------------------------
# 评委打分表单
# -----------------------------

def show_scoring_form():
    st.subheader("📝 请为每位参赛者打分（满分100分）")
    st.markdown("📌 **评分标准**：")
    for category, max_score in weights.items():
        st.markdown(f"- **{category}**：满分 {max_score} 分")

    new_scores = []

    with st.form(key="scoring_form"):
        for participant in participants:
            with st.expander(f"🎤 {participant['姓名']} (编号: {participant['编号']})", expanded=True):
                score_row = {
                    "评委ID": st.session_state.judge_id,
                    "device_id": device_id,  # ✅ 记录设备ID
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
                            key=f"{participant['编号']}_{category}",
                            help=f"本项满分 {max_score} 分"
                        )
                        score_row[category] = score
                        total += score

                score_row["总分"] = total
            st.caption(f"✅ {participant['姓名']} 当前总分：{total} / {MAX_TOTAL}")
            new_scores.append(score_row)

        submitted = st.form_submit_button("📤 提交所有评分")

        if submitted:
            # 后端校验
            for row in new_scores:
                for category, max_score in weights.items():
                    if not (0 <= row[category] <= max_score):
                        st.error(f"❌ {category} 分数超出范围（应为 0~{max_score}）")
                        return

            # 再次检查是否已提交
            if has_submitted(device_id):
                st.error("⚠️ 您的设备已提交过评分，不可重复提交。")
                st.session_state.has_submitted = True
                return

            # 保存评分
            new_df = pd.DataFrame(new_scores)
            global all_scores
            all_scores = pd.concat([all_scores, new_df], ignore_index=True)
            save_scores(all_scores)

            st.session_state.has_submitted = True
            st.success("🎉 感谢您的评分！数据已提交。每个设备仅可提交一次。")

# -----------------------------
# 发布者查看最终得分
# -----------------------------

def display_final_scores_publisher():
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 最终得分（仅发布者可见）")

    if all_scores.empty or all_scores["总分"].sum() == 0:
        st.sidebar.info("📭 暂无评分数据")
        return

    # ✅ 安全处理 device_id 列
    if "device_id" in all_scores.columns:
        score_df = all_scores[all_scores["device_id"] != ""]  # 过滤空值
    else:
        score_df = all_scores

    if score_df.empty or score_df["总分"].sum() == 0:
        st.sidebar.info("📭 暂无有效评分数据")
        return

    # 计算平均分
    final_scores = score_df.groupby(["编号", "姓名"])["总分"].agg(
        平均分=("mean"),
        评委人数=("count"),
        最高分=("max"),
        最低分=("min")
    ).round(2).reset_index()

    final_scores = final_scores.sort_values(by="平均分", ascending=False).reset_index(drop=True)
    final_scores.insert(0, "排名", final_scores.index + 1)

    st.sidebar.dataframe(final_scores, use_container_width=True)
    st.sidebar.bar_chart(final_scores.set_index("姓名")["平均分"])

    # 导出数据
    csv = score_df.to_csv(index=False)
    st.sidebar.download_button(
        "💾 导出原始评分数据 (CSV)",
        csv,
        "朗诵比赛评分数据.csv",
        "text/csv"
    )

# -----------------------------
# 启动应用
# -----------------------------

if __name__ == "__main__":
    main()
