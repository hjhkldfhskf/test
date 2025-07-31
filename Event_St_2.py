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

# 发布者密码（建议修改为更安全的密码）
PUBLISHER_PASSWORD = "admin123"  # ← 请修改为你的密码

# -----------------------------
# 工具函数
# -----------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_scores():
    if os.path.exists(SCORES_FILE):
        return pd.read_csv(SCORES_FILE)
    else:
        return pd.DataFrame(columns=["评委ID", "编号", "姓名"] + list(weights.keys()) + ["总分"])

def save_scores(df):
    df.to_csv(SCORES_FILE, index=False)

def clear_scores():
    if os.path.exists(SCORES_FILE):
        os.remove(SCORES_FILE)

# -----------------------------
# 初始化状态
# -----------------------------

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "judge_id" not in st.session_state:
    st.session_state.judge_id = f"J{len(load_scores()['评委ID'].unique()) + 1:03d}"

# 加载评分数据
all_scores = load_scores()

# -----------------------------
# 页面主函数
# -----------------------------

def main():
    st.title("🎙️ 技术党支部朗诵活动打分表（匿名在线评分）")

    # 显示评分入口
    if st.session_state.submitted:
        st.success("✅ 感谢您的评分！您已成功提交，不可重复提交。")
    else:
        show_scoring_form()

    # 管理区：发布者登录
    st.sidebar.title("🔐 发布者管理")
    pwd = st.sidebar.text_input("请输入发布者密码", type="password")
    
    if st.sidebar.button("登录"):
        if hash_password(pwd) == hash_password(PUBLISHER_PASSWORD):
            st.session_state.publisher_logged_in = True
            st.sidebar.success("登录成功！")
        else:
            st.sidebar.error("密码错误")

    # 发布者功能（仅登录后可见）
    if st.session_state.get("publisher_logged_in", False):
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 管理功能")

        # 显示统计
        st.sidebar.write(f"✅ 已收到 {len(all_scores['评委ID'].unique())} 份评分")
        st.sidebar.write(f"🎯 共 {len(participants)} 位参赛者")

        # 一键清除
        if st.sidebar.button("🗑️ 一键清除所有评分"):
            clear_scores()
            st.session_state.submitted = False
            st.session_state.publisher_logged_in = False
            st.cache_data.clear()
            st.sidebar.success("✅ 所有评分已清除，可重新开始")
            st.experimental_rerun()  # 重新加载页面

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

            # 保存评分
            new_df = pd.DataFrame(new_scores)
            global all_scores
            all_scores = pd.concat([all_scores, new_df], ignore_index=True)
            save_scores(all_scores)
            st.session_state.submitted = True
            st.success("🎉 感谢您的评分！数据已提交。")

# -----------------------------
# 发布者查看最终得分
# -----------------------------

def display_final_scores_publisher():
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 最终得分（仅发布者可见）")

    if all_scores.empty:
        st.sidebar.info("📭 暂无评分数据")
        return

    # 计算平均分
    final_scores = all_scores.groupby(["编号", "姓名"])["总分"].agg(
        平均分=("mean"),
        评委人数=("count"),
        最高分=("max"),
        最低分=("min")
    ).round(2).reset_index()

    final_scores = final_scores.sort_values(by="平均分", ascending=False).reset_index(drop=True)
    final_scores.insert(0, "排名", final_scores.index + 1)

    st.sidebar.dataframe(final_scores, use_container_width=True)

    # 图表
    st.sidebar.bar_chart(final_scores.set_index("姓名")["平均分"])

    # 可选：导出数据
    if st.sidebar.download_button(
        "💾 导出评分数据 (CSV)",
        all_scores.to_csv(index=False),
        "朗诵比赛评分数据.csv",
        "text/csv"
    ):
        st.sidebar.success("导出成功")

# -----------------------------
# 启动应用
# -----------------------------

if __name__ == "__main__":
    main()
