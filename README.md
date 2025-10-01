# VelaChat 后端服务

![VelaChat Logo](./logo.png)

> **注意**：此logo中的元素由绘制而成，和"微信"无关

这是一个基于FastAPI开发的HTTP API服务，作为VelaChat软件的后端。VelaChat是一款专为小米/Redmi手表设计的智能聊天应用，提供便捷的微信消息管理和智能手表交互功能。

## 项目简介

VelaChat后端服务为小米/Redmi手表提供强大的微信消息管理能力，支持实时消息同步、智能提醒、快捷回复等功能，让用户在手表上也能轻松管理微信聊天。

## 项目结构

```
velachat-backend/
├── app/                    # 主应用目录
│   ├── api/               # API路由模块
│   │   └── v1/           # API版本1接口
│   ├── models/           # 数据模型定义
│   ├── services/         # 业务逻辑服务
│   ├── utils/            # 工具函数库
│   │   ├── wx_package_manager.py  # 微信包管理器
│   │   ├── pywechat_manager.py    # pywechat管理器
│   │   └── route_condition.py     # 条件路由装饰器
│   └── main.py           # 应用入口文件
├── config.yaml           # 主配置文件
├── pyproject.toml        # 项目依赖配置
├── run.bat               # Windows启动脚本
├── start-server.py       # 服务器启动脚本
└── static/               # 静态资源文件
    ├── swagger-ui/       # API文档界面
    └── redoc/            # 备用API文档
```

## 快速开始

### 环境要求

| 环境 | 版本 |
| :----: | :--: |
| OS | [![Windows](https://img.shields.io/badge/Windows-10%7C11%7CServer2016+-white?logo=windows&logoColor=white)](https://www.microsoft.com/) |
| 微信 | [![微信](https://img.shields.io/badge/%E5%BE%AE%E4%BF%A1-3.9.X-07c160?logo=wechat&logoColor=white)](https://pan.baidu.com/s/1FvSw0Fk54GGvmQq8xSrNjA?pwd=vsmj) |
| Python | [![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/) |

- Python 3.9+
- Windows操作系统（微信客户端运行环境）
- 微信桌面版已安装并登录

### 配置设置
编辑 `config.yaml` 文件进行基本配置：

```yaml
# VelaChat后端配置
package: "wxauto"  # 微信自动化包版本 (wxauto/wxautox/pywechat)

server:
  host: "0.0.0.0"   # 服务器监听地址
  port: 8000        # 服务器监听端口
  reload: true      # 开发模式热重载

auth:
  token: "your-secret-token"  # API访问令牌

database:
  type: "sqlite"    # 数据库类型
  path: "data/velachat.db"  # 数据库文件路径

wechat:
  app_path: "C:\\Program Files (x86)\\Tencent\\WeChat\\WeChat.exe"  # 微信安装路径
```

### 启动服务
```bash
# Windows系统
run.bat

# 或手动启动
python start-server.py
```

### API文档访问
服务启动后，可以通过以下地址访问API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 配置说明

### 主要配置文件
- `config.yaml` - 主配置文件（服务器设置、数据库配置等）
- `pyproject.toml` - 项目依赖管理

### 重要配置项说明
- `package` - 微信自动化包版本选择
- `server.port` - API服务端口（默认8000）
- `auth.token` - API访问安全令牌
- `database.path` - 数据库文件存储路径

## 故障排除

### 常见问题
1. **微信连接失败**：检查微信是否已登录，路径配置是否正确
2. **端口被占用**：修改config.yaml中的端口号
3. **权限不足**：以管理员权限运行服务

### 日志查看
服务日志位于 `logs/` 目录，可通过日志文件排查问题。

## 许可证

本项目采用 AGPL-3.0 许可证，详见 LICENSE 文件。

## 致谢

本项目基于以下优秀的开源项目构建，特此感谢：

- **[pywechat](https://github.com/Hello-Mr-Crab/pywechat)** - 强大的微信RPA自动化工具
- **[wxauto](https://github.com/cluic/wxauto)** - Windows微信客户端自动化库
- **[wxauto-restful-api](https://github.com/cluic/wxauto-restful-api)** - wxauto的RESTful API服务

感谢这些开源项目的贡献者们为微信自动化领域做出的卓越贡献。

---

**VelaChat - 让智能手表聊天更便捷**
