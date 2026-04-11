---
globs: tests/**/*.py
---

# 测试规范

## 文件命名
- 测试文件：`test_<module_name>.py`，不加 `_new`、`_v2` 后缀
- 测试目录结构与源码目录对应

## 编写规则
- 修改代码后必须跑 `pytest tests/ -v` 全量验证
- 不能只跑改动文件的测试
- mock 目标要跟实际调用路径一致（如 `collectors.arxiv.requests.get` → `patch.object(collector, '_session')`）
- RSS 等时间相关测试用动态日期，不硬编码

## 测试覆盖
- 新增模块必须有对应测试
- 测试至少覆盖：正常路径、异常路径、边界条件
