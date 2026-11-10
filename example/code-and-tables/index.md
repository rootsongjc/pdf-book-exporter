---
title: 代码与表格
weight: 20
part_id: part-basics
---

代码块使用 Typst 内置的语法高亮；表格带斑马纹，可以跨页断开。两者都是技术书籍里最容易出排版问题的地方。

## 代码块

### 内联代码

在文本中使用 `console.log()` 或者 `print()` 这样的内联代码。中文文本中的 `代码片段` 测试。

### Python 代码块

```python
# Python 代码示例 - 数据处理
import pandas as pd
import numpy as np
from datetime import datetime

def process_data(filename):
    """
    处理 CSV 数据文件
    Args:
        filename (str): 文件名
    Returns:
        pd.DataFrame: 处理后的数据
    """
    # 读取数据
    df = pd.read_csv(filename, encoding='utf-8')
    
    # 数据清洗
    df = df.dropna()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 数据转换
    df['value'] = df['value'].astype(float)
    
    return df

# 使用示例
if __name__ == "__main__":
    data = process_data('sample.csv')
    print(f"处理了 {len(data)} 条记录 😄")
```

这是代码块下面的文字，用来确认代码块与后续段落之间的间距。

### JavaScript 代码块

```javascript
// JavaScript 代码示例 - React 组件
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const DataFetcher = ({ apiUrl }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await axios.get(apiUrl);
        setData(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [apiUrl]);

  if (loading) return '加载中...';
  if (error) return `错误：${error}`;
  
  return [
    '数据展示',
    JSON.stringify(data, null, 2)
  ];

export default DataFetcher;
```

长代码块允许在页面底部断开并在下一页继续，不会整块被推到下一页而留下大片空白。

### Mermaid 图

Hugo 在浏览器里渲染 Mermaid；印刷版保留源码，作为纯文本代码块显示：

```mermaid
flowchart LR
  md[Markdown] --> pandoc[Pandoc] --> typ[Typst] --> pdf[PDF]
```

### 超宽代码块

```bash
# 这是一个非常长的命令行示例，用来测试PDF中超宽代码块的处理效果
docker run -d --name my-container --restart=unless-stopped -p 8080:80 -v /host/path/to/data:/container/data -e ENV_VAR_1=value1 -e ENV_VAR_2=value2 -e ENV_VAR_3=value3 --network=my-network --memory=2g --cpus=1.5 my-image:latest
```

## 表格

### 基础表格

| 姓名 | 年龄 | 职业 | 城市 |
|------|------|------|------|
| 张三 | 28 | 工程师 | 北京 |
| 李四 | 32 | 设计师 | 上海 |
| 王五 | 25 | 产品经理 | 深圳 |

### 包含格式的表格

| 功能 | 状态 | 优先级 | 负责人 | 备注 |
|------|------|--------|--------|------|
| **用户登录** | ✅ 完成 | 🔴 高 | @张三 | 已上线 |
| *数据导出* | 🔄 进行中 | 🟡 中 | @李四 | 预计下周完成 |
| ~~旧功能~~ | ❌ 废弃 | 🔵 低 | - | 不再维护 |
| `API接口` | ⏳ 计划中 | 🟠 中 | @王五 | 需求评审中 |

### 复杂表格（包含代码和链接）

| 技术栈 | 版本 | 用途 | 示例代码 | 文档链接 |
|--------|------|------|----------|----------|
| React | 18.2.0 | 前端框架 | `<Component />` | [官方文档](https://react.dev) |
| Node.js | 18.17.0 | 后端运行时 | `require('express')` | [Node.js](https://nodejs.org) |
| Python | 3.11 | 数据处理 | `import pandas` | [Python.org](https://python.org) |
| Docker | 24.0 | 容器化，开发者友好，支持多平台，可以在 Linux、Windows 和 macOS 上运行，可以用 Orbstack 替代 | `docker build .` | [Docker Hub](https://hub.docker.com) |

### 包含内联代码和中文混排的表格

| 匹配方式 | 描述 | 示例 |
|----------|------|------|
| `prefix` | 前缀必须与 `:path` 头的开头匹配 | `/hello` 匹配 `/hello`、`/helloworld`、`/hello/v1` |
| `path` | 路径必须与 `:path` 头完全匹配 | `/hello` 只匹配 `/hello`，不匹配 `/helloworld` |
| `safe_regex` | 使用正则表达式匹配 `:path` 头 | `/\d{3}` 匹配三位数字路径 |
| `connect_matcher` | 只匹配 CONNECT 请求 | 用于 HTTP CONNECT 方法 |

### 跨页的长表格

| 序号 | 名称 | 说明 |
|------|------|------|
| 1 | 条目 1 | 第 1 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 2 | 条目 2 | 第 2 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 3 | 条目 3 | 第 3 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 4 | 条目 4 | 第 4 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 5 | 条目 5 | 第 5 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 6 | 条目 6 | 第 6 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 7 | 条目 7 | 第 7 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 8 | 条目 8 | 第 8 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 9 | 条目 9 | 第 9 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 10 | 条目 10 | 第 10 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 11 | 条目 11 | 第 11 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 12 | 条目 12 | 第 12 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 13 | 条目 13 | 第 13 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 14 | 条目 14 | 第 14 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 15 | 条目 15 | 第 15 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 16 | 条目 16 | 第 16 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 17 | 条目 17 | 第 17 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 18 | 条目 18 | 第 18 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 19 | 条目 19 | 第 19 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 20 | 条目 20 | 第 20 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 21 | 条目 21 | 第 21 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 22 | 条目 22 | 第 22 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 23 | 条目 23 | 第 23 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 24 | 条目 24 | 第 24 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 25 | 条目 25 | 第 25 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 26 | 条目 26 | 第 26 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 27 | 条目 27 | 第 27 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 28 | 条目 28 | 第 28 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 29 | 条目 29 | 第 29 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 30 | 条目 30 | 第 30 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 31 | 条目 31 | 第 31 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 32 | 条目 32 | 第 32 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 33 | 条目 33 | 第 33 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 34 | 条目 34 | 第 34 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 35 | 条目 35 | 第 35 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 36 | 条目 36 | 第 36 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 37 | 条目 37 | 第 37 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 38 | 条目 38 | 第 38 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 39 | 条目 39 | 第 39 行，用于检查斑马纹和表头在跨页时是否正确延续 |
| 40 | 条目 40 | 第 40 行，用于检查斑马纹和表头在跨页时是否正确延续 |
