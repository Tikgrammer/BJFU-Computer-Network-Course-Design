import socket
import time
import struct
import random
import string  # 导入string模块，用于处理字符串
import sys  # 导入sys模块，用于退出程序

# 配置参数
TIMEOUT = 0.1  # 100ms 超时
RETRIES = 2  # 重传次数
NUM_PACKETS = 12  # 发送报文数量
VERSION = 2  # 版本号
# 用于计算server的总体响应时间
first_response_time = None
last_response_time = None


def is_valid_ip(ip):
    """验证IP地址格式"""
    try:
        socket.inet_aton(ip)
        # inet_aton是将IPv4地址字符串转换成32位的二进制格式
        # 如果不是有效的IPv4地址，就会抛出异常
        return True  # 如果成功，则IP地址有效
    except socket.error:  # 如果发生错误，则IP地址无效
        return False


def validate_arguments(server_ip, server_port):
    """验证命令行参数"""
    if not is_valid_ip(server_ip):  # 检查IP地址是否有效
        print(f"无效的 IP 地址: {server_ip}")  # 打印无效IP地址错误信息
        sys.exit(1)  # 退出程序
    if not (0 <= server_port <= 65535):  # 检查端口号是否在有效范围内
        print(f"无效的端口号: {server_port}. 端口号必须在0到65535之间")  # 打印无效端口号错误信息
        sys.exit(1)  # 退出程序


def initialize_socket():
    """初始化socket"""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 创建UDP套接字
    client_socket.settimeout(TIMEOUT)  # 设置套接字超时时间
    return client_socket  # 返回套接字对象


def create_packet(seq_num):
    """创建数据包"""
    # 这个函数是后面重传数据与原本数据相同的关键
    # 生成随机数据并编码为字节串
    random_data = ''.join(random.choices(string.ascii_lowercase + string.digits, k=200)).encode('utf-8')
    packet = struct.pack('!H B 200s', seq_num, VERSION, random_data)  # 打包报文数据
    return packet


def send_packet(client_socket, packet, server_ip, server_port):
    """发送报文并接收响应"""
    global first_response_time
    global last_response_time  # 声明全局变量
    if first_response_time is None:
        first_response_time = time.time()
    start_time = time.time()  # 记录发送时间
    client_socket.sendto(packet, (server_ip, server_port))  # 发送报文

    try:
        response, _ = client_socket.recvfrom(4096)  # 接收服务器响应
        end_time = time.time()  # 记录接收时间
        rtt = (end_time - start_time) * 1000  # 计算RTT (单位:ms)
        seq_no, ver, sys_time = struct.unpack('!H B 200s', response)  # 解包响应报文
        sys_time = sys_time.decode('utf-8').rstrip('\x00')  # 解码并清理系统时间字段
        print(f"序号: {seq_no}, 服务器 IP:端口: {server_ip}:{server_port}, RTT: {rtt:.2f}ms, 服务器时间: {sys_time}")
        # time.sleep(1)

        if last_response_time is None:
            last_response_time = time.time()
        else:
            last_response_time = max(last_response_time, time.time())

        return rtt, True  # 返回RTT值和成功标志
    except socket.timeout:
        # 超时处理
        # 只关心数据包前两个字节的序列号，并且只关心第一个元素，也就是序号
        print(f"序号: {struct.unpack('!H', packet[:2])[0]}, 请求超时")  # 打印超时信息
        return None, False  # 返回失败标志
    except struct.error as e:
        # 解包错误处理
        print(f"解包响应报文时出错: {e}")  # 打印解包错误信息
        return None, False  # 返回失败标志
    except Exception as e:
        # 其他异常处理
        print(f"接收响应报文时出错: {e}")  # 打印接收错误信息
        return None, False  # 返回失败标志


def calculate_statistics(rtts):
    """计算并打印RTT统计信息"""
    max_rtt = max(rtts)  # 计算最大RTT
    min_rtt = min(rtts)  # 计算最小RTT
    avg_rtt = sum(rtts) / len(rtts)  # 计算平均RTT
    std_dev_rtt = (sum((x - avg_rtt) ** 2 for x in rtts) / len(rtts)) ** 0.5  # 计算RTT的标准差
    print(f"最大RTT: {max_rtt:.2f}ms")  # 打印最大RTT
    print(f"最小RTT: {min_rtt:.2f}ms")  # 打印最小RTT
    print(f"平均RTT: {avg_rtt:.2f}ms")  # 打印平均RTT
    print(f"RTT标准差: {std_dev_rtt:.2f}ms")  # 打印RTT的标准差


def main():
    if len(sys.argv) != 3:  # 检查输入参数的个数
        print("输入的参数个数不是3个，请重新输入。")
        sys.exit(1)

    server_ip = sys.argv[1]  # 获取服务器IP地址
    try:
        # 判断端口号是否为整数，增强代码的健壮性
        server_port = int(sys.argv[2])  # 获取服务器端口号
    except ValueError:
        print("端口号必须是整数。")
        sys.exit(1)

    validate_arguments(server_ip, server_port)  # 验证命令行参数

    client_socket = initialize_socket()  # 初始化套接字

    received_packets = 0  # 初始化接收报文计数器
    rtts = []  # 初始化RTT列表

    global first_response_time
    global last_response_time
    try:
        for i in range(1, NUM_PACKETS + 1):  # 循环发送报文
            packet = create_packet(i)  # 创建数据包
            for attempt in range(RETRIES + 1):  # 重传机制
                # 发送报文并检查是否成功
                rtt, success = send_packet(client_socket, packet, server_ip, server_port)
                if success:  # 如果成功接收响应
                    received_packets += 1  # 增加接收报文计数
                    rtts.append(rtt)  # 保存RTT值
                    break  # 成功接收则退出重传循环
                elif attempt == RETRIES:  # 检查是否达到最大重传次数
                    print(f"序号: {i}, 请求失败，共重传 {RETRIES} 次")  # 打印重传失败信息
    finally:
        # 确保套接字在异常情况下也能被关闭
        client_socket.close()

    if rtts:  # 如果接收到响应报文
        print(f"接收到的UDP报文数量: {received_packets}")  # 打印接收报文数
        print(f"丢包率: {(1 - received_packets / NUM_PACKETS) * 100:.2f}%")  # 打印丢包率
        calculate_statistics(rtts)  # 计算并打印RTT统计信息

        response_time_difference = last_response_time - first_response_time
        print(f"服务器整体响应时间之差: {response_time_difference * 1000:.2f}ms")


    else:
        print("未接收到任何报文。")  # 如果没有接收到任何报文，打印相应信息


if __name__ == '__main__':
    main()  # 调用主函数
