import io
from typing import Any, List

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from review_service import analyze_reviews_from_dataframe, generate_coze_input_markdown


app = FastAPI(
    title="Store Review Analysis API",
    description="门店评论分析与自动回复 Agent 的 API 服务",
    version="0.1.0"
)


class ReviewItem(BaseModel):
    review_id: int = Field(..., description="评论编号")
    rating: float = Field(..., ge=1, le=5, description="评分，范围为 1-5 分")
    content: str = Field(..., min_length=1, description="评论内容不能为空")


class ReviewAnalyzeRequest(BaseModel):
    reviews: List[ReviewItem] = Field(..., min_length=1, description="评论列表不能为空")


def make_json_safe(value: Any) -> Any:
    """
    将 Pandas / NumPy 里可能出现的特殊数字类型，
    转换成普通 Python 类型，避免 API 返回 JSON 时出错。
    """
    if isinstance(value, dict):
        return {key: make_json_safe(val) for key, val in value.items()}

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    if hasattr(value, "item"):
        return value.item()

    return value


@app.get("/")
def root():
    return {
        "message": "Store Review Analysis API is running.",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "store-review-analysis-api"
    }


@app.post("/analyze_reviews")
def analyze_reviews(request: ReviewAnalyzeRequest):
    """
    接收评论列表，返回评论统计、差评分类和问题分布。
    """
    try:
        reviews_data = [review.model_dump() for review in request.reviews]
        df = pd.DataFrame(reviews_data)

        result = analyze_reviews_from_dataframe(df)
        safe_result = make_json_safe(result)

        return {
            "success": True,
            "message": "评论分析完成",
            "data": safe_result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误：{str(e)}")
    
@app.post("/generate_coze_input")
def generate_coze_input(request: ReviewAnalyzeRequest):
    """
    接收评论列表，返回可直接复制到 Coze / Dify 的 Markdown 输入文本。
    """
    try:
        reviews_data = [review.model_dump() for review in request.reviews]
        df = pd.DataFrame(reviews_data)

        analysis_result = analyze_reviews_from_dataframe(df)
        markdown_text = generate_coze_input_markdown(analysis_result)

        return {
            "success": True,
            "message": "Coze 经营分析输入文本生成完成",
            "markdown": markdown_text
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误：{str(e)}")
    
@app.post("/upload_reviews_csv")
async def upload_reviews_csv(file: UploadFile = File(...)):
    """
    上传 CSV 文件，返回评论统计、差评分类和问题分布结果。
    """
    try:
        # 1. 校验文件类型
        if not file.filename.endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail="仅支持上传 CSV 文件"
            )

        # 2. 读取上传文件内容
        file_content = await file.read()

        # 3. 处理中文编码
        try:
            text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = file_content.decode("gbk")

        # 4. 用 pandas 读取 CSV
        df = pd.read_csv(io.StringIO(text))

        # 5. 调用已有评论分析逻辑
        result = analyze_reviews_from_dataframe(df)

        return {
            "success": True,
            "message": "CSV 文件评论分析完成",
            "filename": file.filename,
            "data": result
        }

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误：{str(e)}")
    
@app.post("/upload_reviews_csv_generate_markdown")
async def upload_reviews_csv_generate_markdown(file: UploadFile = File(...)):
    """
    上传 CSV 文件，返回可直接复制到 Coze / Dify 的 Markdown 输入文本。
    """
    try:
        # 1. 校验文件类型
        if not file.filename.endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail="仅支持上传 CSV 文件"
            )

        # 2. 读取上传文件内容
        file_content = await file.read()

        # 3. 处理中文编码
        try:
            text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = file_content.decode("gbk")

        # 4. 用 pandas 读取 CSV
        df = pd.read_csv(io.StringIO(text))

        # 5. 调用已有评论分析逻辑
        analysis_result = analyze_reviews_from_dataframe(df)

        # 6. 生成 Coze / Dify 可用 Markdown
        markdown_text = generate_coze_input_markdown(analysis_result)

        return {
            "success": True,
            "message": "CSV 文件已分析，并生成 Coze / Dify 输入文本",
            "filename": file.filename,
            "markdown": markdown_text
        }

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误：{str(e)}")
    
@app.post("/upload_reviews_csv_markdown_text", response_class=PlainTextResponse)
async def upload_reviews_csv_markdown_text(file: UploadFile = File(...)):
    """
    上传 CSV 文件，直接返回 Markdown 纯文本，方便复制到 Coze / Dify。
    """
    try:
        # 1. 校验文件类型
        if not file.filename.endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail="仅支持上传 CSV 文件"
            )

        # 2. 读取上传文件内容
        file_content = await file.read()

        # 3. 处理中文编码
        try:
            text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = file_content.decode("gbk")

        # 4. 用 pandas 读取 CSV
        df = pd.read_csv(io.StringIO(text))

        # 5. 调用已有评论分析逻辑
        analysis_result = analyze_reviews_from_dataframe(df)

        # 6. 生成 Markdown
        markdown_text = generate_coze_input_markdown(analysis_result)

        return markdown_text

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误：{str(e)}")