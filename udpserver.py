import socket  # 导入socket模块，创建和操作网络连接
import random  # 导入random模块，用于模拟丢包
import struct  # 导入struct模块，用于打包和解包二进制数据
import time  # 导入time模块，用于获取和格式化系统时间

# 配置参数
SERVER_IP = '0.0.0.0'  # 表示监听所有接口
SERVER_PORT = 33909  # 服务器端口
LOSS_RATE = 0.3  # 实际丢包概率要考虑重传次数


# 初始化 socket
def initialize_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 创建UDP套接字
    # 第一个参数指定地址族，即使用IPv4地址。
    # 第二个参数指定套接字类型，即UDP套接字。
    server_socket.bind((SERVER_IP, SERVER_PORT))  # 绑定套接字到指定地址和端口
    print(f"服务器监听于 {SERVER_IP} : {SERVER_PORT}")  # 打印服务器监听信息
    return server_socket  # 返回套接字对象


# 处理客户端请求
def handle_request(request, client_address, server_socket):
    # request是客户端请求的二进制数据
    try:
        seq_no, ver, message = struct.unpack('!H B 200s', request)  # 解包请求报文
        # ! 网络字节序为大端序，即高字节存储在低地址。
        # H 表示无符号短整型2字节  B表示无符号字符 1字节
        # 200s 表示长度为200的字符串
    except struct.error as e:
        # 捕获在解包过程中可能出现的异常
        print(f"解包请求报文时出错: {e}")  # 打印解包错误信息
        return

    if random.random() < LOSS_RATE:  # 模拟丢包
        print(f"序号: {seq_no}, 报文丢失")  # 打印丢包信息
        return

    server_time = time.strftime('%H-%M-%S').encode('utf-8')  # 获取当前系统时间并编码为字节串
    try:
        response = struct.pack('!H B 200s', seq_no, ver, server_time)  # 打包响应报文
        server_socket.sendto(response, client_address)  # 发送响应报文
        print(f"序号: {seq_no}, 响应已发送")  # 打印响应发送信息
        print("报文信息：", message)  # 打印接收到的报文信息
    except struct.error as e:
        # 打包过程错误处理
        print(f"打包响应报文时出错: {e}")  # 打印打包错误信息
    except Exception as e:
        # 其他异常处理
        print(f"发送响应报文时出错: {e}")  # 打印发送错误信息


# 主函数
def main():
    server_socket = initialize_socket()  # 初始化套接字
    try:
        while True:  # 循环接收和处理客户端请求
            try:
                request, client_address = server_socket.recvfrom(4096)  # 接收客户端请求
                handle_request(request, client_address, server_socket)  # 处理客户端请求
            except Exception as e:  # 异常处理
                print(f"接收客户端请求时出错: {e}")  # 打印接收错误信息
    finally:
        # 确保套接字在异常情况下也能被关闭
        server_socket.close()
        print("服务器已关闭")  # 打印服务器关闭信息


if __name__ == '__main__':
    main()
