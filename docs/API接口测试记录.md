# 项目3：门店评论分析 API 接口测试记录

## 一、测试目标

本测试用于验证“门店评论分析与自动回复 Agent”的 API 接口是否能够接收评论 JSON 数据，并返回结构化分析结果。

本轮测试重点验证两类能力：

1. 正常输入情况下，接口是否能正确返回评论统计、差评数量、问题分类统计和差评明细；
2. 异常输入情况下，接口是否能返回明确的参数校验错误，而不是程序直接崩溃。

本项目原始版本是 Python 本地脚本，通过读取 CSV 文件完成评论分析。本次 API 版改造后，评论分析能力被封装为 FastAPI 接口，可以通过 JSON 请求调用。

---

## 二、接口信息

- 接口名称：门店评论分析接口
- 请求方式：POST
- 接口路径：`/analyze_reviews`
- 本地测试地址：`http://127.0.0.1:8000/docs`
- 输入格式：JSON
- 输出格式：JSON
- 接口文档工具：FastAPI Swagger UI

---

## 三、接口输入字段说明

接口接收一个评论列表，字段结构如下：

```json
{
  "reviews": [
    {
      "review_id": 1,
      "rating": 5,
      "content": "评论内容"
    }
  ]
}
```

字段说明：

| 字段名 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| review_id | int | 是 | 评论编号 |
| rating | float | 是 | 评论评分，范围为 1-5 |
| content | string | 是 | 评论正文，不能为空 |
| reviews | list | 是 | 评论列表，至少包含 1 条评论 |

---

## 四、测试用例与测试结果

### 测试1：正常评论数据测试

#### 测试目的

验证接口在输入正常评论数据时，是否能够成功返回评论统计、分类统计和差评明细。

#### 测试输入

本次输入 4 条评论，其中：

- 1 条好评；
- 3 条差评；
- 差评分别涉及等待时间、配送物流、服务态度三个问题类型。

```json
{
  "reviews": [
    {
      "review_id": 1,
      "rating": 5,
      "content": "拿铁口感很顺滑，店员推荐也很耐心，整体体验不错"
    },
    {
      "review_id": 2,
      "rating": 2,
      "content": "等了二十多分钟才拿到咖啡，赶时间的话不太方便"
    },
    {
      "review_id": 3,
      "rating": 1,
      "content": "外卖送到的时候杯子漏了，袋子里全是咖啡"
    },
    {
      "review_id": 4,
      "rating": 2,
      "content": "服务员态度比较冷淡，问问题的时候有点不耐烦"
    }
  ]
}
```

#### 预期结果

- 状态码：200；
- success：true；
- total_reviews：4；
- average_rating：2.5；
- positive_count：1；
- neutral_count：0；
- negative_count：3；
- negative_percentage：75.0%；
- 差评分类应包含等待时间、配送物流、服务态度。

#### 实际结果

状态码：200

```json
{
  "success": true,
  "message": "评论分析完成",
  "data": {
    "basic_stats": {
      "total_reviews": 4,
      "average_rating": 2.5,
      "positive_count": 1,
      "neutral_count": 0,
      "negative_count": 3,
      "positive_percentage": "25.0%",
      "neutral_percentage": "0.0%",
      "negative_percentage": "75.0%"
    },
    "category_summary": [
      {
        "category": "产品质量",
        "count": 1,
        "percentage": "25.0%"
      },
      {
        "category": "等待时间",
        "count": 1,
        "percentage": "25.0%"
      },
      {
        "category": "配送物流",
        "count": 1,
        "percentage": "25.0%"
      },
      {
        "category": "服务态度",
        "count": 1,
        "percentage": "25.0%"
      }
    ],
    "negative_category_summary": [
      {
        "category": "等待时间",
        "count": 1,
        "percentage": "33.3%"
      },
      {
        "category": "配送物流",
        "count": 1,
        "percentage": "33.3%"
      },
      {
        "category": "服务态度",
        "count": 1,
        "percentage": "33.3%"
      }
    ],
    "negative_reviews": [
      {
        "review_id": 2,
        "rating": 2,
        "content": "等了二十多分钟才拿到咖啡，赶时间的话不太方便",
        "category": "等待时间"
      },
      {
        "review_id": 3,
        "rating": 1,
        "content": "外卖送到的时候杯子漏了，袋子里全是咖啡",
        "category": "配送物流"
      },
      {
        "review_id": 4,
        "rating": 2,
        "content": "服务员态度比较冷淡，问问题的时候有点不耐烦",
        "category": "服务态度"
      }
    ]
  }
}
```

#### 测试结论

通过。

接口能够正确接收 4 条评论数据，并返回基础统计、评论分类统计、差评分类统计和差评明细。

---

### 测试2：空评论列表测试

#### 测试目的

验证当用户传入空评论列表时，接口是否能够拦截异常输入。

#### 测试输入

```json
{
  "reviews": []
}
```

#### 预期结果

- 状态码：422；
- 接口应提示评论列表至少需要包含 1 条数据；
- 程序不应崩溃。

#### 实际结果

状态码：422

```json
{
  "detail": [
    {
      "type": "too_short",
      "loc": [
        "body",
        "reviews"
      ],
      "msg": "List should have at least 1 item after validation, not 0",
      "input": [],
      "ctx": {
        "field_type": "List",
        "min_length": 1,
        "actual_length": 0
      }
    }
  ]
}
```

#### 测试结论

通过。

接口成功识别了空评论列表，并返回 422 参数校验错误，说明 `reviews` 字段的最小长度校验生效。

---

### 测试3：评分超出范围测试

#### 测试目的

验证当用户传入超出 1-5 范围的评分时，接口是否能够拦截异常输入。

#### 测试输入

```json
{
  "reviews": [
    {
      "review_id": 1,
      "rating": 6,
      "content": "这条评论评分不合法"
    }
  ]
}
```

#### 预期结果

- 状态码：422；
- 接口应提示 rating 需要小于等于 5；
- 程序不应继续进入评论分析逻辑。

#### 实际结果

状态码：422

```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": [
        "body",
        "reviews",
        0,
        "rating"
      ],
      "msg": "Input should be less than or equal to 5",
      "input": 6,
      "ctx": {
        "le": 5
      }
    }
  ]
}
```

#### 测试结论

通过。

接口成功识别了评分超出范围的问题，并返回 422 参数校验错误，说明 `rating` 的 1-5 分范围限制生效。

---

### 测试4：评论内容为空测试

#### 测试目的

验证当用户传入空评论内容时，接口是否能够拦截异常输入。

#### 测试输入

```json
{
  "reviews": [
    {
      "review_id": 1,
      "rating": 3,
      "content": ""
    }
  ]
}
```

#### 预期结果

- 状态码：422；
- 接口应提示 content 至少需要 1 个字符；
- 程序不应继续进入评论分析逻辑。

#### 实际结果

状态码：422

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": [
        "body",
        "reviews",
        0,
        "content"
      ],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {
        "min_length": 1
      }
    }
  ]
}
```

#### 测试结论

通过。

接口成功识别了评论内容为空的问题，并返回 422 参数校验错误，说明 `content` 的非空校验生效。

---

## 五、测试结果汇总

| 测试编号 | 测试场景 | 输入情况 | 预期状态码 | 实际状态码 | 是否通过 |
|---|---|---|---|---|---|
| 测试1 | 正常评论数据 | 4 条评论，1 条好评，3 条差评 | 200 | 200 | 通过 |
| 测试2 | 空评论列表 | reviews 为空数组 | 422 | 422 | 通过 |
| 测试3 | 评分超出范围 | rating = 6 | 422 | 422 | 通过 |
| 测试4 | 评论内容为空 | content = "" | 422 | 422 | 通过 |

---

## 六、本轮测试结论

本轮测试验证了门店评论分析 API 的基础可用性和输入校验能力。

在正常输入情况下，接口能够成功返回：

- 评论总数；
- 平均评分；
- 好评 / 中评 / 差评数量；
- 好评 / 中评 / 差评占比；
- 全部评论分类统计；
- 差评问题分类统计；
- 差评明细列表。

在异常输入情况下，接口能够对以下问题进行拦截：

- 空评论列表；
- 评分超出 1-5 范围；
- 评论内容为空。

本次测试说明，项目已从原来的本地 Python 脚本进一步升级为具备基础参数校验能力的 API 服务。相比原始脚本版本，API 版不仅能在本地终端运行，也可以通过 JSON 请求被 Swagger、前端页面、工作流工具或其他系统调用。

---

## 七、当前接口能力说明

当前 API 版已经具备以下能力：

1. 接收 JSON 格式评论数据；
2. 对评论字段进行基础校验；
3. 对评分进行范围限制；
4. 对空评论内容进行拦截；
5. 调用评论分析逻辑并返回结构化 JSON；
6. 输出基础统计、问题分类和差评明细；
7. 通过 Swagger 页面完成接口测试。

---

## 八、当前局限

当前版本仍属于学习型 API 原型，存在以下局限：

1. 暂未接入数据库，评论数据主要通过请求体传入；
2. 暂未支持 CSV 文件上传接口；
3. 评论分类仍基于关键词规则，复杂语义下可能存在误判；
4. 暂未接入 Coze / 大模型 API 自动生成经营周报；
5. 暂未进行前端页面封装；
6. 暂未部署到云端服务器。

---

## 九、后续优化方向

后续可以继续优化：

1. 增加 CSV 文件上传接口；
2. 增加自动生成 Markdown 周报输入文件的接口；
3. 接入 Coze / 大模型 API，自动生成经营分析报告；
4. 增加数据库，用于保存历史评论和分析记录；
5. 增加可视化图表展示评论趋势；
6. 增加更准确的 AI 语义分类能力；
7. 将接口部署到云端，支持外部访问。

---

## 十、面试表达总结

本项目原始版本是一个本地 Python 评论分析脚本，主要通过读取 CSV 文件完成评论统计、差评筛选和问题分类。

在 API 版改造中，我将核心评论分析逻辑拆分到 `review_service.py` 中，并使用 FastAPI 在 `main.py` 中封装了 `POST /analyze_reviews` 接口。接口可以接收 JSON 格式评论数据，返回评论统计、问题分类和差评明细等结构化结果。

通过本次改造，我理解了脚本和 API 服务的区别，也初步掌握了 FastAPI、Pydantic 参数校验、JSON 请求响应和 Swagger 接口测试。这个改造让项目从“只能本地运行的脚本”进一步接近真实业务系统中的接口服务。