import streamlit as st
import pandas as pd
import os

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

# 评分权重（最大分值）
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

# 加载已有评分数据
if os.path.exists(SCORES_FILE):
    all_scores = pd.read_csv(SCORES_FILE)
else:
    all_scores = pd.DataFrame(columns=["评委ID", "编号", "姓名"] + list(weights.keys()) + ["总分"])

# 初始化 session_state
if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "judge_id" not in st.session_state:
    st.session_state.judge_id = f"J{len(all_scores['评委ID'].unique()) + 1:03d}"

# -----------------------------
# 页面主函数
# -----------------------------

def main():
    st.title("🎙️ 技术党支部朗诵活动打分表（匿名在线评分）")

    # 显示当前评委状态
    if st.session_state.submitted:
        st.success("✅ 感谢您的评分！您已成功提交，不可重复提交。")
    else:
        show_scoring_form()

    # 显示最终得分
    st.markdown("---")
    display_final_scores()

# -----------------------------
# 打分表单（带分值限制和提示）
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

            # 显示该选手预估总分
            st.caption(f"✅ {participant['姓名']} 当前总分：{total} / {MAX_TOTAL}")

            new_scores.append(score_row)

        submitted = st.form_submit_button("📤 提交所有评分")

        if submitted:
            # ✅ 后端二次校验（防前端篡改）
            valid = True
            for row in new_scores:
                for category, max_score in weights.items():
                    if not (0 <= row[category] <= max_score):
                        st.error(f"❌ {category} 分数超出范围（应为 0~{max_score}）")
                        valid = False
            if not valid:
                st.stop()

            # 保存评分
            new_df = pd.DataFrame(new_scores)
            global all_scores
            all_scores = pd.concat([all_scores, new_df], ignore_index=True)
            all_scores.to_csv(SCORES_FILE, index=False)
            st.session_state.submitted = True
            st.success("🎉 感谢您的评分！数据已提交。")

# -----------------------------
# 显示最终得分（平均总分）
# -----------------------------

def display_final_scores():
    st.subheader("📊 参赛者最终得分（平均总分）")

    if all_scores.empty:
        st.info("📭 暂无评分数据")
        return

    # 计算每位参赛者的平均总分
    final_scores = all_scores.groupby(["编号", "姓名"])["总分"].agg(
        平均分=("mean"),
        评委人数=("count"),
        最高分=("max"),
        最低分=("min")
    ).round(2).reset_index()

    # 排名
    final_scores = final_scores.sort_values(by="平均分", ascending=False).reset_index(drop=True)
    final_scores.insert(0, "排名", final_scores.index + 1)

    st.dataframe(final_scores, use_container_width=True)

    # 柱状图
    st.bar_chart(final_scores.set_index("姓名")["平均分"])

# -----------------------------
# 启动应用
# -----------------------------

if __name__ == "__main__":
    main()
