#!/usr/bin/env python3
"""
统一启动脚本
支持IPv4/IPv6双栈网络访问
"""
import uvicorn
import socket
import subprocess
import sys
import os
import argparse
from app.utils.config import Settings

def get_network_info():
    """获取网络信息"""
    network_info = {
        "ipv4_addresses": [],
        "ipv6_addresses": [],
        "hostname": socket.gethostname()
    }
    
    try:
        # 获取IPv4地址
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ipv4 = s.getsockname()[0]
        network_info["ipv4_addresses"].append(local_ipv4)
        s.close()
    except:
        pass
    
    try:
        # 获取IPv6地址
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.connect(("2001:4860:4860::8888", 80))
        local_ipv6 = s.getsockname()[0]
        network_info["ipv6_addresses"].append(local_ipv6)
        s.close()
    except:
        pass
    
    # 获取所有网络接口地址
    try:
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            current_interface = None
            for line in lines:
                line = line.strip()
                if line and not line.startswith(' '):
                    current_interface = line
                elif 'IPv4 地址' in line or 'IPv4 Address' in line:
                    ip = line.split(':')[-1].strip()
                    if ip and ip not in network_info["ipv4_addresses"] and not ip.startswith('127.'):
                        network_info["ipv4_addresses"].append(ip)
                elif 'IPv6 地址' in line or 'IPv6 Address' in line:
                    ip = line.split(':')[-1].strip()
                    if ip and ip not in network_info["ipv6_addresses"] and not ip.startswith('fe80') and '%' not in ip:
                        network_info["ipv6_addresses"].append(ip)
    except:
        pass
    
    return network_info

def check_and_install_dependencies():
    """检查并安装依赖"""
    print("📦 检查依赖...")
    
    # 检查Python环境
    try:
        import sys
        print(f"✅ Python版本: {sys.version}")
    except:
        print("❌ Python环境异常")
        return False
    
    # 检查必要依赖
    dependencies = {
        'uvicorn': 'uvicorn',
        'fastapi': 'fastapi',
        'pydantic': 'pydantic',
        'pyyaml': 'pyyaml'
    }
    
    missing_deps = []
    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {module} 已安装")
        except ImportError:
            missing_deps.append(package)
            print(f"❌ {module} 未安装")
    
    # 安装缺失的依赖
    if missing_deps:
        print(f"📦 安装缺失的依赖: {', '.join(missing_deps)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_deps)
            print("✅ 依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
            return False
    else:
        print("✅ 所有依赖都已安装")
        return True

def check_ipv6_support():
    """检查系统是否支持IPv6"""
    try:
        socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        return True
    except:
        return False

def print_usage():
    """打印使用说明"""
    print("""
🚀 WXAuto API 统一启动脚本 - 使用说明

📋 基本用法:
  python start-server.py [选项]

🔧 选项:
  -c, --config CONFIG    指定配置文件 (默认: config.yaml)
  --host HOST           监听地址 (默认: 0.0.0.0 - IPv4)
  -p, --port PORT       监听端口 (默认: 8000)
  --reload              启用热重载
  --check-deps          检查并安装依赖
  --ipv6                强制使用IPv6模式
  -h, --help            显示帮助信息

🌐 网络模式:
  # 默认IPv4模式 (推荐)
  python start-server.py
  
  # 强制IPv6模式
  python start-server.py --ipv6
  
  # 指定IPv4地址
  python start-server.py --host 0.0.0.0
  
  # 指定IPv6地址
  python start-server.py --host ::

📝 配置文件说明:
  修改 config.yaml 中的 server.host 为 "::" 启用IPv6
  或者使用命令行参数 --host :: 或 --ipv6
""")

def main():
    """统一启动主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='WXAuto API 统一启动脚本')
    parser.add_argument('--config', '-c', default='config.yaml', 
                       help='配置文件路径 (默认: config.yaml)')
    parser.add_argument('--host', default=None, 
                       help='监听地址 (默认: 0.0.0.0 - IPv4)')
    parser.add_argument('-p', '--port', type=int, default=8000, 
                       help='监听端口 (默认: 8000)')
    parser.add_argument('--reload', action='store_true', 
                       help='启用热重载')
    parser.add_argument('--check-deps', action='store_true', 
                       help='检查并安装依赖')
    parser.add_argument('--ipv6', action='store_true', 
                       help='强制使用IPv6模式')
    
    args = parser.parse_args()
    
    print("🌐 启动 WXAuto API 服务")
    print("=" * 60)
    
    # 检查并安装依赖
    if args.check_deps:
        if not check_and_install_dependencies():
            sys.exit(1)
    
    # 检查IPv6支持
    ipv6_supported = check_ipv6_support()
    print(f"IPv6支持状态: {'✅ 支持' if ipv6_supported else '❌ 不支持'}")
    
    # 加载配置
    try:
        settings = Settings.load_config(args.config)
        print(f"✅ 已加载配置文件: {args.config}")
    except:
        settings = Settings()
        print("⚠️  使用默认配置")
    
    # 确定监听地址
    if args.ipv6:
        host = "::"
        print("🌐 使用IPv6模式")
    elif args.host:
        host = args.host
        print(f"🌐 使用指定地址: {host}")
    else:
        # 默认使用IPv4模式，更安全兼容
        host = "0.0.0.0"
        print("🌐 默认使用IPv4模式 (0.0.0.0)")
        if ipv6_supported:
            print("💡 提示: 系统支持IPv6，如需使用请添加 --ipv6 参数")
    
    # 使用命令行参数或配置文件设置
    port = args.port if args.port != 8000 else settings.server.port
    reload = args.reload if args.reload else settings.server.reload
    
    # 获取网络信息
    network_info = get_network_info()
    
    print("\n📡 网络信息:")
    print(f"主机名: {network_info['hostname']}")
    print(f"监听地址: {host}")
    print(f"监听端口: {port}")
    
    if network_info["ipv4_addresses"]:
        print("IPv4地址:")
        for ip in network_info["ipv4_addresses"]:
            print(f"  - http://{ip}:{port}")
    
    if network_info["ipv6_addresses"]:
        print("IPv6地址:")
        for ip in network_info["ipv6_addresses"]:
            print(f"  - http://[{ip}]:{port}")
    
    print(f"\n🌐 访问地址:")
    if host == '::':
        print(f"  IPv6/IPv4: http://[::]:{port}")
    else:
        print(f"  监听地址: http://{host}:{port}")
    print(f"  本地测试: http://localhost:{port}")
    
    print("\n📋 API文档地址:")
    if network_info["ipv4_addresses"]:
        for ip in network_info["ipv4_addresses"]:
            print(f"  Swagger: http://{ip}:{port}/docs")
            print(f"  ReDoc: http://{ip}:{port}/redoc")
    
    if network_info["ipv6_addresses"]:
        for ip in network_info["ipv6_addresses"]:
            print(f"  Swagger: http://[{ip}]:{port}/docs")
            print(f"  ReDoc: http://[{ip}]:{port}/redoc")
    
    print("=" * 60)
    print("🔧 服务器配置:")
    print(f"  监听地址: {host}")
    print(f"  端口: {port}")
    print(f"  热重载: {'启用' if reload else '禁用'}")
    print("=" * 60)
    
    try:
        # 启动服务器
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n⏹️  服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 如果没有参数，直接启动服务（默认IPv4模式）
    if len(sys.argv) == 1:
        print("🚀 启动 WXAuto API 服务 (IPv4模式)")
        print("💡 如需查看帮助，请使用: python start-server.py --help")
        print("🌐 如需IPv6模式，请使用: python start-server.py --ipv6")
        print("=" * 60)
        # 直接启动，不检查依赖
        main()
    else:
        main()