---
title: 进阶格式
weight: 40
part_id: part-hugo
---

本章包含数学公式、任务列表和定义列表，并带有一个嵌套的子章节（5.4 版式细节）。子章节来自 `advanced/layout/index.md`，本页则是 `advanced/_index.md`。

## 数学公式

### 内联公式

在文本中，我们可以使用内联公式，比如 $E = mc^2$ 或者 $\pi \approx 3.14159$。

中文文本中的数学公式：圆的面积公式是 $A = \pi r^2$，其中 $r$ 是半径。

### 块级公式

$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$

$$
\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}
$$

### LaTeX 环境

\begin{align}
\nabla \times \vec{\mathbf{B}} -\, \frac1c\, \frac{\partial\vec{\mathbf{E}}}{\partial t} &= \frac{4\pi}{c}\vec{\mathbf{j}} \\
\nabla \cdot \vec{\mathbf{E}} &= 4 \pi \rho \\
\nabla \times \vec{\mathbf{E}}\, +\, \frac1c\, \frac{\partial\vec{\mathbf{B}}}{\partial t} &= \vec{\mathbf{0}} \\
\nabla \cdot \vec{\mathbf{B}} &= 0
\end{align}

## 任务列表

### 项目进度跟踪

- [x] 需求分析 ✅
- [x] 技术选型 ✅
- [x] 架构设计 ✅
- [ ] 前端开发 🔄
  - [x] 页面设计
  - [x] 组件开发
  - [ ] 接口对接
  - [ ] 测试验证
- [ ] 后端开发 ⏳
  - [x] 数据库设计
  - [ ] API 开发
  - [ ] 业务逻辑
  - [ ] 性能优化
- [ ] 测试阶段 ⏳
- [ ] 部署上线 ⏳

### 学习计划

- [x] **第一周**：基础知识
  - [x] HTML/CSS 复习
  - [x] JavaScript ES6+
  - [x] React 基础
- [ ] **第二周**：进阶内容
  - [x] React Hooks
  - [ ] 状态管理 (Redux/Zustand)
  - [ ] 路由管理
- [ ] **第三周**：实战项目
  - [ ] 项目搭建
  - [ ] 功能开发
  - [ ] 测试部署

## 定义列表

### 技术术语

API
: Application Programming Interface，应用程序编程接口，是不同软件组件之间通信的规范。

REST
: Representational State Transfer，表现层状态转换，是一种软件架构风格。

GraphQL
: 一种用于 API 的查询语言和运行时，由 Facebook 开发。

### 编程概念

函数式编程
: 一种编程范式，将计算视为数学函数的求值，避免状态变化和可变数据。

面向对象编程
: 基于"对象"概念的编程范式，对象包含数据（属性）和代码（方法）。
