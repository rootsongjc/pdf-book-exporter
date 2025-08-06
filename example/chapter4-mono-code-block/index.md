---
title: SourceHanMono 字体测试
weight: 40
---

本文档用于验证 SourceHanMono 字体在代码块中的应用效果。

## Python 代码示例

```python
def hello_world():
    """
    一个简单的函数，展示 SourceHanMono 字体效果
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

## 内联代码测试

以下是内联代码的测试：

- Python 变量：`变量名 = "中文值"`
- 文件路径：`/home/用户/文档/测试文件.txt`
- 命令示例：`ls -la 中文目录`
- 混合内容：`hello世界test`

## 等宽字符对齐测试

```
ASCII字符:  ABCDEFGHIJKLMNOPQRSTUVWXYZ
中文字符:   你好世界测试字体显示效果验证
日文字符:   こんにちはテストフォント
韩文字符:   안녕하세요테스트폰트
混合内容:   Test测试テストテスト
```

## 代码注释多语言测试

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

此文档将帮助验证 SourceHanMono 字体是否正确应用于所有代码块和内联代码。
