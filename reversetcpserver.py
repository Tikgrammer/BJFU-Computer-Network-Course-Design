import socket
import struct
import threading


# 处理客户端连接
def handle_client(client_socket):
    """
    处理客户端连接请求的函数
    client_socket: 客户端套接字对象
    """
    try:
        init_packet = client_socket.recv(6)  # 接收Initialization报文，接收6个字节的数据
        init_type, block_count = struct.unpack('!HI', init_packet)  # 解包Initialization报文
        # ! 表示大端序，即高位字节存在于存储器的低地址端
        # H 表示一个无符号短整型 2字节
        # I 表示一个无符号整型 4字节
        # 前2个字节表示init_type
        # 4个字节表示block_count
        if init_type != 1:  # 检查报文类型是否为Initialization
            return

        agree_packet = struct.pack('!H', 2)  # 构造agree报文
        # 构建一个类型为2的 大端序 无符号短整型2字节 的agree报文
        client_socket.sendall(agree_packet)  # 发送agree报文给客户端

        for _ in range(block_count):  # 逐块处理数据
            request_packet = client_socket.recv(6)  # 接收reverseRequest报文
            request_type, length = struct.unpack('!HI', request_packet)  # 解包reverseRequest报文
            if request_type != 3:  # 检查报文类型是否为reverseRequest
                return
            data = client_socket.recv(length).decode('ascii')  # 接收数据块
            reversed_data = data[::-1]  # 反转数据块
            # 构造reverseAnswer报文
            answer_packet = struct.pack('!HI', 4, length) + reversed_data.encode('ascii')
            client_socket.sendall(answer_packet)  # 发送reverseAnswer报文

    finally:
        print("断开 ", client_socket.getpeername(), " 的连接")
        client_socket.close()  # 关闭客户端连接


# 主函数
def main():
    """
    主函数，用于创建服务器套接字、接受客户端连接，并创建新线程处理客户端连接请求
    """
    server_ip = '0.0.0.0'  # 监听所有IP地址
    server_port = 33909  # 监听端口号

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建TCP套接字
    server_socket.bind((server_ip, server_port))  # 绑定IP地址和端口
    server_socket.listen(5)  # 开始监听，最大长度是5，第6个及以后的连接请求将会被拒绝
    print(f"服务器正在监听 {server_ip} : {server_port}")

    while True:
        client_socket, addr = server_socket.accept()  # 接受客户端连接
        # 创建新线程处理客户端连接
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        # args=(client_socket,)将client_socket作为参数传递给handle_client函数
        print("来自 ", client_socket.getpeername(), " 的连接")
        client_handler.start()  # 启动线程


if __name__ == '__main__':
    main()
