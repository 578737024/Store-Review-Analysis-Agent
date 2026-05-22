from pathlib import Path
from typing import Dict, List, Any

import pandas as pd


CATEGORY_KEYWORDS = {
    "配送物流": ["外卖", "配送", "送到", "漏", "少送", "袋子", "骑手"],
    "等待时间": ["等", "等待", "排队", "很久", "二十多分钟", "出餐", "重新做"],
    "服务态度": ["服务员", "态度", "冷淡", "不耐烦", "服务"],
    "环境卫生": ["地面", "桌子", "桌面", "脏", "清理", "卫生"],
    "产品质量": ["咖啡", "味道", "口感", "淡", "浓", "拿铁", "美式", "产品"],
    "价格问题": ["价格", "贵", "偏高", "性价比"],
    "空间体验": ["环境", "座位", "安静", "插座", "办公", "空间", "挤"],
}


def classify_review(content: str) -> str:
    """
    根据评论内容进行简单关键词分类。

    当前版本是规则分类，不是 AI 语义分类。
    优点：简单、可解释、容易调试。
    缺点：复杂语义下可能分类不准确。
    """
    if not isinstance(content, str) or not content.strip():
        return "其他"

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in content:
                return category

    return "其他"


def get_sentiment_label(rating: float) -> str:
    """
    根据评分判断好评 / 中评 / 差评。
    """
    if rating >= 4:
        return "好评"
    elif rating == 3:
        return "中评"
    else:
        return "差评"


def calculate_percentage(count: int, total: int) -> str:
    """
    计算百分比，返回字符串形式，例如 40.0%。
    """
    if total == 0:
        return "0.0%"
    return f"{count / total * 100:.1f}%"


def build_category_summary(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    统计评论分类数量和占比。
    """
    total = len(df)

    if total == 0:
        return []

    summary_df = (
        df["category"]
        .value_counts()
        .reset_index()
    )

    summary_df.columns = ["category", "count"]
    summary_df["percentage"] = summary_df["count"].apply(
        lambda x: calculate_percentage(x, total)
    )

    return summary_df.to_dict(orient="records")


def analyze_reviews_from_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    核心分析函数。

    输入：DataFrame 评论数据
    输出：字典格式分析结果，未来可以直接作为 API 的 JSON 返回。
    """
    required_columns = {"review_id", "rating", "content"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"缺少必要字段：{', '.join(missing_columns)}")

    # 复制一份，避免修改原始数据
    df = df.copy()

    # 确保 rating 是数字
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df.dropna(subset=["rating"])

    # 评论分类
    df["category"] = df["content"].apply(classify_review)

    # 情感标签
    df["sentiment"] = df["rating"].apply(get_sentiment_label)

    total_reviews = len(df)
    average_rating = float(round(df["rating"].mean(), 1)) if total_reviews > 0 else 0.0

    positive_count = len(df[df["sentiment"] == "好评"])
    neutral_count = len(df[df["sentiment"] == "中评"])
    negative_count = len(df[df["sentiment"] == "差评"])

    negative_df = df[df["sentiment"] == "差评"].copy()

    result = {
        "basic_stats": {
            "total_reviews": total_reviews,
            "average_rating": average_rating,
            "positive_count": positive_count,
            "neutral_count": neutral_count,
            "negative_count": negative_count,
            "positive_percentage": calculate_percentage(positive_count, total_reviews),
            "neutral_percentage": calculate_percentage(neutral_count, total_reviews),
            "negative_percentage": calculate_percentage(negative_count, total_reviews),
        },
        "category_summary": build_category_summary(df),
        "negative_category_summary": build_category_summary(negative_df),
        "negative_reviews": negative_df[
            ["review_id", "rating", "content", "category"]
        ].to_dict(orient="records"),
    }

    return result


def analyze_reviews_from_csv(csv_path: str) -> Dict[str, Any]:
    """
    从 CSV 文件读取评论数据并分析。
    """
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{csv_path}")

    df = pd.read_csv(path)
    return analyze_reviews_from_dataframe(df)

def generate_coze_input_markdown(analysis_result: Dict[str, Any]) -> str:
    """
    根据评论分析结果生成给 Coze / Dify 使用的 Markdown 输入文本。
    """
    basic_stats = analysis_result["basic_stats"]
    category_summary = analysis_result["category_summary"]
    negative_category_summary = analysis_result["negative_category_summary"]
    negative_reviews = analysis_result["negative_reviews"]

    lines = []

    lines.append("# 门店评论经营分析输入")
    lines.append("")

    lines.append("## 一、基础数据")
    lines.append(f"- 评论总数：{basic_stats['total_reviews']}")
    lines.append(f"- 平均评分：{basic_stats['average_rating']}")
    lines.append(f"- 好评数量：{basic_stats['positive_count']}")
    lines.append(f"- 中评数量：{basic_stats['neutral_count']}")
    lines.append(f"- 差评数量：{basic_stats['negative_count']}")
    lines.append(f"- 好评占比：{basic_stats['positive_percentage']}")
    lines.append(f"- 中评占比：{basic_stats['neutral_percentage']}")
    lines.append(f"- 差评占比：{basic_stats['negative_percentage']}")
    lines.append("")

    lines.append("## 二、全部评论分类统计")
    if category_summary:
        for item in category_summary:
            lines.append(
                f"- {item['category']}：{item['count']}条，占比{item['percentage']}"
            )
    else:
        lines.append("- 暂无分类统计数据")
    lines.append("")

    lines.append("## 三、差评问题分类统计")
    if negative_category_summary:
        for item in negative_category_summary:
            lines.append(
                f"- {item['category']}：{item['count']}条，占比{item['percentage']}"
            )
    else:
        lines.append("- 暂无差评分类统计数据")
    lines.append("")

    lines.append("## 四、典型差评明细")
    if negative_reviews:
        for review in negative_reviews:
            lines.append(
                f"- 评论ID {review['review_id']}｜评分：{review['rating']}｜分类：{review['category']}｜内容：{review['content']}"
            )
    else:
        lines.append("- 暂无差评数据")
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
    lines.append("- 回复话术要真诚、克制、不甩锅、不夸大承诺；")
    lines.append("- 不要虚构门店已经完成的整改动作；")
    lines.append("- 不要承诺退款、赔偿、免单等未确认事项。")

    return "\n".join(lines)

if __name__ == "__main__":
    result = analyze_reviews_from_csv("data/store_reviews.csv")

    print("====== API可调用的评论分析结果 ======")
    print(result)