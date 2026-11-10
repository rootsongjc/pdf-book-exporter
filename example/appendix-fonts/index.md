---
title: 字体与等宽字符
weight: 100
part_id: part-appendix
---

附录中的章节编号为 A、B……，小节为 A.1、A.2，图表为「图 A-1」。本附录检查代码块中的 CJK 字符：等宽字体通常不含汉字，Typst 会按字体回退链补齐（默认 JetBrains Mono → Menlo → … → Noto Sans Mono CJK SC），中文字符应与 ASCII 字符基线对齐。

## 字体回退链

| 用途 | 中文预设 | 英文预设 |
|------|----------|----------|
| 正文 | Noto Sans CJK SC → Source Han Sans SC → PingFang SC → Microsoft YaHei → Noto Sans | Noto Sans → Helvetica Neue → Arial → Noto Sans CJK SC |
| 代码 | JetBrains Mono → Menlo → DejaVu Sans Mono → Consolas → Noto Sans Mono CJK SC | 同左 |

未安装的字体会在编译前被剔除，因此不会产生警告；用 `--font` / `--monofont` 或 `book.font` 可以完全覆盖预设。

## Python 代码示例

```python
def hello_world():
    """
    一个简单的函数，展示等宽字体中的 CJK 回退效果
    """
    print("Hello, 世界！")  # 中文注释
    print("こんにちは、世界！")  # 日文注释
    print("안녕하세요, 세계!")  # 韩文注释
    
    # 数字和符号测试
    numbers = [1, 2, 3, 4, 5]
    symbols = ['!', '@', '#', '$', '%', '^', '&', '*']
    
    return "测试成功"
```

## Bash 脚本示例

```bash
#!/bin/bash
# 这是一个包含中文的脚本

echo "开始执行脚本..."
echo "正在处理中文文件名：测试文档.txt"

# 创建包含中文路径的目录
mkdir -p "./测试目录/子目录"
ls -la "./测试目录"

# 函数定义
function 显示消息() {
    echo "函数名也可以是中文：$1"
}

显示消息 "这是一个测试消息"
```

## JavaScript 代码示例

```javascript
// JavaScript 中的中文变量和注释
const 问候语 = "你好，世界！";
const 数字列表 = [1, 2, 3, 4, 5];

function 显示问候(名字) {
    console.log(`${问候语} ${名字}`);
    // 这里展示中文字符在等宽字体中的效果
    console.log("中文字符测试：测试");
    console.log("English text: test");
    console.log("混合文本：mix 测试 test");
}

显示问候("张三");
```

## 内联代码

以下是内联代码的测试：

- Python 变量：`变量名 = "中文值"`
- 文件路径：`/home/用户/文档/测试文件.txt`
- 命令示例：`ls -la 中文目录`
- 混合内容：`hello世界test`

## 等宽字符对齐

```
ASCII字符:  ABCDEFGHIJKLMNOPQRSTUVWXYZ
中文字符:   你好世界测试字体显示效果验证
日文字符:   こんにちはテストフォント
韩文字符:   안녕하세요테스트폰트
混合内容:   Test测试テストテスト
```

## 多语言注释

```go
package main

import "fmt"

// 主函数 - 中文注释
// メイン関数 - 日文注释
// 메인 함수 - 韩文注释
func main() {
    // 变量声明
    message := "多语言字体测试"
    
    fmt.Println(message)
    fmt.Println("Hello, 世界！")       // 英文 + 中文
    fmt.Println("こんにちは、世界！")   // 日文
    fmt.Println("안녕하세요, 세계!")   // 韩文
}
```
