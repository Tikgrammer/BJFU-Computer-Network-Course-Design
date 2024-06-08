import socket
import struct
import random
import sys
import time


# 读取文件内容并返回
def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"文件 '{file_path}' 不存在。")
        sys.exit(1)
    except Exception as e:
        print(f"读取文件时出现错误: {e}")
        sys.exit(1)


# 将数据分割成指定范围的块长度
def split_data(data, min_len, max_len):
    """
    将数据分割成指定范围的块长度
    data: 待分割的数据
    min_len: 最小块长度
    max_len: 最大块长度
    指定范围内随机长度的列表
    """
    lengths = []
    while len(data) > 0:
        length = random.randint(min_len, max_len)
        length = min(length, len(data))
        lengths.append(length)
        data = data[length:]
    return lengths


# 发送数据块并接收反转后的数据块
def send_data(server_ip, server_port, data, min_len, max_len):
    """
    发送数据块并接收反转后的数据块，并将反转后的数据拼接成完整文件并写入txt文件
    server_ip: 服务器IP地址
    server_port: 服务器端口号
    data: 待发送的数据
    min_len: 最小块长度
    max_len: 最大块长度
    """
    try:
        lengths = split_data(data, min_len, max_len)
        n = len(lengths)
        reversed_chunks = []  # 用于保存反转后的块

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, server_port))

            init_packet = struct.pack('!HI', 1, n)
            s.sendall(init_packet)

            agree_packet = s.recv(2)
            agree_type, = struct.unpack('!H', agree_packet)
            # 这样确保agree_type是整数的格式   没有逗号的话agree_type是元组

            if agree_type != 2:
                print("没有收到服务器的确认报文。")
                return

            start = 0
            for i, length in enumerate(lengths):
                end = start + length
                chunk = data[start:end]
                reverse_request_packet = struct.pack('!HI', 3, length) + chunk.encode('ascii')
                s.sendall(reverse_request_packet)

                reverse_answer_packet = s.recv(6 + length)
                _, _, reversed_chunk = struct.unpack(f'!HI{length}s', reverse_answer_packet)
                reversed_chunks.append(reversed_chunk)  # 保存反转后的块
                print(f"第 {i + 1} 块: {reversed_chunk.decode('ascii')}")  # 打印反转后的块内容

                start = end

        # 将反转后的块拼接成完整文件内容
        reversed_data = b"".join(reversed_chunks).decode('ascii')

        # 创建txt文件并写入反转后的数据
        with open("reversed_file.txt", "w") as file:
            file.write(reversed_data)
            print("文件已保存为 'reversed_file.txt'。")
    except socket.error as e:
        print(f"网络连接错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"发送数据时出现错误: {e}")
        sys.exit(1)


# 主函数
def main():
    """
    主函数，用于解析命令行参数，并调用发送数据的函数

    Args:
    无

    Returns:
    无
    """
    if len(sys.argv) != 6:
        print(f"用法: {sys.argv[0]} <服务器IP> <服务器端口> <文件路径> <最小块长度> <最大块长度>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = sys.argv[2]
    file_path = sys.argv[3]
    min_len = sys.argv[4]
    max_len = sys.argv[5]

    try:
        # 验证服务器IP地址格式
        socket.inet_aton(server_ip)
    except socket.error:
        print("无效的服务器IP地址。")
        sys.exit(1)

    # 验证服务器端口号是否为整数
    try:
        server_port = int(server_port)
    except ValueError:
        print("服务器端口号必须是整数。")
        sys.exit(1)

    if server_port < 0 or server_port > 65535:
        print("端口号必须在0~65535区间范围内。")
        sys.exit(1)

    # 验证最小块长度是否为整数
    try:
        min_len = int(min_len)
    except ValueError:
        print("最小块长度必须是整数。")
        sys.exit(1)

    # 验证最大块长度是否为整数
    try:
        max_len = int(max_len)
    except ValueError:
        print("最大块长度必须是整数。")
        sys.exit(1)

    # 验证是否为负数
    if min_len < 0 or max_len < 0:
        print("min_len和max_len都不能是负数。")
        sys.exit(1)

    # 验证最小块长度是否小于等于最大块长度
    if min_len > max_len:
        print("块长度不能为负数。")
        sys.exit(1)

    data = read_file(file_path)  # 读取文件内容
    send_data(server_ip, server_port, data, min_len, max_len)  # 发送数据


if __name__ == '__main__':
    main()
