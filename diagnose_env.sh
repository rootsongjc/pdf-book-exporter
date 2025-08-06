#!/bin/bash

echo "=== 终端环境诊断脚本 ==="
echo "运行时间: $(date)"
echo "用户: $(whoami)"
echo "Shell: $0 ($SHELL)"
echo "工作目录: $(pwd)"
echo ""

echo "=== PATH信息 ==="
echo "PATH长度: ${#PATH} 字符"
echo "TeX路径:"
echo "$PATH" | tr ':' '\n' | grep -E "(tex|latex)" | head -5
echo ""

echo "=== LaTeX环境 ==="
echo "LuaLaTeX位置: $(which lualatex)"
echo "LuaLaTeX版本:"
lualatex --version 2>/dev/null | head -2 || echo "❌ LuaLaTeX不可用"
echo ""

echo "=== Pandoc环境 ==="  
echo "Pandoc位置: $(which pandoc)"
echo "Pandoc版本:"
pandoc --version 2>/dev/null | head -1 || echo "❌ Pandoc不可用"
echo ""

echo "=== 字体环境 ==="
echo "字体缓存:"
fc-list 2>/dev/null | grep -E "(Source Han|PingFang|Noto)" | wc -l | awk '{print $1 " 个相关字体"}'
echo ""

echo "=== LaTeX包状态 ==="
echo "检查关键包:"
for pkg in fontspec xeCJK luatexja; do
    if kpsewhich $pkg.sty >/dev/null 2>&1; then
        echo "✅ $pkg.sty 已安装"
    else
        echo "❌ $pkg.sty 未找到"
    fi
done
echo ""

echo "=== 工作目录文件 ==="
echo "关键文件存在性:"
for file in ../template.tex ../cli.py ../filters/emoji-passthrough.lua; do
    if [ -f "$file" ]; then
        echo "✅ $(basename $file) 存在 ($(stat -f%z "$file") bytes)"
    else
        echo "❌ $(basename $file) 缺失"
    fi
done
echo ""

echo "=== 临时目录权限 ==="
temp_dir=$(python3 -c "import tempfile; print(tempfile.gettempdir())")
echo "临时目录: $temp_dir"
echo "权限: $(ls -ld "$temp_dir" 2>/dev/null || echo '无法访问')"
echo ""

echo "=== 环境变量 ==="
echo "相关环境变量:"
env | grep -E "(TEXMF|LUA|PANDOC|LANG|LC_)" | sort
echo ""

echo "=== 测试简单命令 ==="
echo "测试LaTeX字体命令:"
echo '\documentclass{article}\usepackage{fontspec}\begin{document}测试\end{document}' > /tmp/test_font.tex
if lualatex -interaction=nonstopmode -output-directory=/tmp /tmp/test_font.tex >/dev/null 2>&1; then
    echo "✅ LuaLaTeX字体测试成功"
else
    echo "❌ LuaLaTeX字体测试失败"
fi
rm -f /tmp/test_font.*
echo ""

echo "=== 诊断建议 ==="
echo "如果在新终端窗口中遇到问题，请："
echo "1. 复制以下命令到新窗口运行此诊断脚本"
echo "2. 对比两个窗口的输出结果"
echo "3. 特别注意PATH、字体和LaTeX包的差异"
echo ""
echo "命令: cd $(pwd) && ./diagnose_env.sh"
