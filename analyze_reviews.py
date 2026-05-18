import pandas as pd
from pathlib import Path


def load_reviews(csv_path: str) -> pd.DataFrame:
    """
    读取门店评论 CSV 文件，并做基础字段检查。
    """
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{csv_path}")

    df = pd.read_csv(path, encoding="utf-8-sig")

    required_columns = ["review_id", "date", "store_name", "rating", "content", "category"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"CSV 缺少必要字段：{missing_columns}")

    return df


def analyze_basic_stats(df: pd.DataFrame) -> dict:
    """
    统计评论总数、平均评分、好评/中评/差评数量。
    """
    total_reviews = len(df)
    average_rating = round(df["rating"].mean(), 2)

    positive_reviews = df[df["rating"] >= 4]
    neutral_reviews = df[df["rating"] == 3]
    negative_reviews = df[df["rating"] <= 2]

    stats = {
        "评论总数": total_reviews,
        "平均评分": average_rating,
        "好评数量": len(positive_reviews),
        "中评数量": len(neutral_reviews),
        "差评数量": len(negative_reviews),
        "好评占比": f"{len(positive_reviews) / total_reviews:.1%}",
        "中评占比": f"{len(neutral_reviews) / total_reviews:.1%}",
        "差评占比": f"{len(negative_reviews) / total_reviews:.1%}",
    }

    return stats


def classify_review(content: str) -> str:
    """
    根据关键词对评论进行简单分类。
    当前版本使用规则分类，后续可以接入 AI 做语义分类。
    """
    content = str(content)

    category_keywords = {
        "配送物流": ["外卖", "漏", "少送", "送到", "袋子", "配送"],
        "等待时间": ["等", "排队", "慢", "二十分钟", "很久", "出餐"],
        "服务态度": ["服务员", "态度", "冷淡", "不耐烦", "服务"],
        "环境卫生": ["脏", "桌面", "地面", "没有及时清理", "杯子还在", "卫生"],
        "产品质量": ["咖啡有点淡", "做成", "味道", "口感", "不好喝", "太淡", "出品"],
        "价格问题": ["价格", "偏高", "贵", "性价比"],
        "空间体验": ["座位", "拥挤", "人太多", "环境", "插座", "音乐"],
    }

    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in content:
                return category

    return "其他"


def add_review_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    为评论添加自动分类结果。
    """
    classified_df = df.copy()
    classified_df["category"] = classified_df["content"].apply(classify_review)
    return classified_df


def filter_negative_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """
    筛选差评：评分小于等于 2 分的评论。
    """
    negative_df = df[df["rating"] <= 2].copy()
    negative_df = negative_df.sort_values(by=["rating", "date"], ascending=[True, True])
    return negative_df


def analyze_category_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    统计各分类数量和占比。
    """
    total_count = len(df)

    category_counts = (
        df["category"]
        .value_counts()
        .reset_index()
    )

    category_counts.columns = ["category", "count"]
    category_counts["percentage"] = category_counts["count"].apply(
        lambda x: f"{x / total_count:.1%}"
    )

    return category_counts


def save_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    保存 DataFrame 到 CSV 文件。
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"文件已导出：{output_path}")


def print_basic_report(stats: dict) -> None:
    """
    打印基础统计报告。
    """
    print("====== 门店评论基础统计报告 ======")
    for key, value in stats.items():
        print(f"{key}：{value}")


def print_category_preview(df: pd.DataFrame) -> None:
    """
    打印评论分类预览。
    """
    print("\n====== 评论分类预览 ======")
    print(df[["review_id", "rating", "content", "category"]])


def print_negative_reviews(negative_df: pd.DataFrame) -> None:
    """
    打印差评预览。
    """
    print("\n====== 差评数据预览 ======")

    if negative_df.empty:
        print("暂无差评数据")
        return

    print(negative_df[["review_id", "date", "rating", "content", "category"]])


def print_category_summary(title: str, summary_df: pd.DataFrame) -> None:
    """
    打印分类统计表。
    """
    print(f"\n====== {title} ======")

    if summary_df.empty:
        print("暂无分类统计数据")
        return

    print(summary_df)

def generate_coze_report_input(
    stats: dict,
    negative_df: pd.DataFrame,
    category_summary_df: pd.DataFrame,
    negative_category_summary_df: pd.DataFrame,
    output_path: str
) -> None:
    """
    生成给 Coze 使用的经营分析输入文本。
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    lines = []

    lines.append("# 门店评论经营分析输入")
    lines.append("")
    lines.append("## 一、基础数据")
    for key, value in stats.items():
        lines.append(f"- {key}：{value}")

    lines.append("")
    lines.append("## 二、全部评论分类统计")
    for _, row in category_summary_df.iterrows():
        lines.append(f"- {row['category']}：{row['count']}条，占比{row['percentage']}")

    lines.append("")
    lines.append("## 三、差评问题分类统计")
    for _, row in negative_category_summary_df.iterrows():
        lines.append(f"- {row['category']}：{row['count']}条，占比{row['percentage']}")

    lines.append("")
    lines.append("## 四、典型差评明细")
    for _, row in negative_df.iterrows():
        lines.append(
            f"- 评论ID {row['review_id']}｜评分：{row['rating']}｜分类：{row['category']}｜内容：{row['content']}"
        )

    lines.append("")
    lines.append("## 五、请基于以上数据完成以下任务")
    lines.append("请你作为门店经营分析助手，基于以上评论数据，输出一份门店评论分析周报。")
    lines.append("")
    lines.append("输出内容包括：")
    lines.append("1. 本周评论整体概况；")
    lines.append("2. 差评主要集中问题；")
    lines.append("3. 每类问题的原因分析；")
    lines.append("4. 优先改进建议；")
    lines.append("5. 针对典型差评的商家回复建议；")
    lines.append("6. 下周门店运营重点。")
    lines.append("")
    lines.append("要求：")
    lines.append("- 不要空泛总结；")
    lines.append("- 必须结合具体数据；")
    lines.append("- 建议要具体可执行；")
    lines.append("- 回复话术要真诚、克制、不甩锅、不夸大承诺。")

    output_file.write_text("\n".join(lines), encoding="utf-8-sig")

    print(f"Coze经营分析输入文本已导出：{output_path}")


def main():
    csv_path = "data/store_reviews.csv"

    classified_output_path = "output/classified_reviews.csv"
    negative_output_path = "output/negative_reviews_classified.csv"
    category_summary_output_path = "output/category_summary.csv"
    negative_category_summary_output_path = "output/negative_category_summary.csv"
    coze_report_input_path = "output/coze_weekly_report_input.md"

    df = load_reviews(csv_path)

    stats = analyze_basic_stats(df)
    print_basic_report(stats)

    classified_df = add_review_category(df)
    print_category_preview(classified_df)

    negative_df = filter_negative_reviews(classified_df)
    print_negative_reviews(negative_df)

    category_summary_df = analyze_category_distribution(classified_df)
    negative_category_summary_df = analyze_category_distribution(negative_df)

    print_category_summary("全部评论分类统计", category_summary_df)
    print_category_summary("差评问题分类统计", negative_category_summary_df)

    save_csv(classified_df, classified_output_path)
    save_csv(negative_df, negative_output_path)
    save_csv(category_summary_df, category_summary_output_path)
    save_csv(negative_category_summary_df, negative_category_summary_output_path)
    generate_coze_report_input(
    stats,
    negative_df,
    category_summary_df,
    negative_category_summary_df,
    coze_report_input_path
)


if __name__ == "__main__":
    main()