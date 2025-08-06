---
title: 代码块和表格测试
weight: 20
lastmod: '2025-08-04'
---

本章节专门测试代码块、表格等复杂格式在 PDF 中的渲染效果。

## 代码块测试

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

这是代码块下面的文字，用来说明代码的用途，比如 Java 代码中的 interface 的实现 theory。

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

这是代码块下方的文字，不应该与代码块重叠，并且要保证上方的代码块可以正确的分页。

弹性云服务器（Elastic Cloud Server）是一种可随时自助获取、可弹性伸缩的云服务器，可帮助您打造可靠、安全、灵活、高效的应用环境，确保服务持久稳定运行，提升运维效率。根据业务发展需要，您可以随时变更规格、切换操作系统、配置安全组规则或调整配额。除此之外，您还可以实时查看监控指标及审计日志，以便及时了解弹性云服务器的健康状态。

### 超宽代码块测试

```bash
# 这是一个非常长的命令行示例，用来测试PDF中超宽代码块的处理效果
docker run -d --name my-container --restart=unless-stopped -p 8080:80 -v /host/path/to/data:/container/data -e ENV_VAR_1=value1 -e ENV_VAR_2=value2 -e ENV_VAR_3=value3 --network=my-network --memory=2g --cpus=1.5 my-image:latest
```

## 表格测试

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

---

*本章节完成了代码块和表格的测试，下一章将测试更多高级格式。*
