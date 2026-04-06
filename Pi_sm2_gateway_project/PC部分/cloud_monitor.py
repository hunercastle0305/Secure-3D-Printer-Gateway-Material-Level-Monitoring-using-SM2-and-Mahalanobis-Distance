import paho.mqtt.client as mqtt
import json
import csv
import os
import time
from gmssl import sm2
import numpy as np

# 1. 配置网关信息
MQTT_BROKER = "test.mosquitto.org"
MQTT_TOPIC = "3DPrinter/monitor/gateway/data_814723"
CSV_FILE = "3D_printer_resin_log.csv"

#使用密钥生产脚本来产生符合条件的密钥，可以自己再修改专属的密钥
PRIVATE_KEY = '123c41e7f818ad4e9e7ea1977c76f9619868734bf9b1af6eb4e42f5404c00df6'
PUBLIC_KEY = '9cb51afa5eb1ceba1eda63c904a2fb99014c5a3d895d01ff1b921001a3b3879f81638a191ef7d2eff035a331d04f27bd071309d5521b5ef9428f863df1184806'

# 强制使用 mode=1，确保 C1C3C2 标准排列，以免发生解码的过程里无法识别的情况
sm2_crypt = sm2.CryptSM2(public_key=PUBLIC_KEY, private_key=PRIVATE_KEY, mode=1)

# 2. 马氏距离算法模型参数
NORMAL_MEAN = np.array([30.0])                   # 假设正常液面距离基准
NORMAL_COV_INV = np.array([[1.0 / (5.0 ** 2)]])  # 正常消耗时的波动方差逆矩阵
THRESHOLD = 3.81                                 # 隐性故障判定阈值

# 3. 初始化持久化存储 (CSV)
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['本地时间', '网关ID', '液面距离(cm)', '异常波动指数(MD)', '供料系统状态'])
    print(f">>> 已创建工业设备运行日志: {CSV_FILE}")

def save_to_csv(data_row):
    """将实时解析的数据落盘"""
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(data_row)

def detect_fault(current_value):
    """在线隐性故障诊断引擎 """
    obs = np.array([current_value])
    m_dist = np.sqrt((obs - NORMAL_MEAN).T @ NORMAL_COV_INV @ (obs - NORMAL_MEAN))
    m_dist_val = round(float(m_dist), 2)

    # 状态判定
    status = "运行正常" if m_dist_val <= THRESHOLD else "🚨 漏液/异常跳变告警"
    return m_dist_val, status

#  4. MQTT 核心拦截与处理逻辑
def on_message(client, userdata, msg):
    try:
        # A. 国密解密
        encrypted_hex = msg.payload.decode('utf-8')
        decrypted_bytes = sm2_crypt.decrypt(bytes.fromhex(encrypted_hex))

        # B. 协议解析 (JSON提取)
        data = json.loads(decrypted_bytes.decode('utf-8'))
        dist_val = data['distance']
        gw_id = data['gw_id']

        # C. 算法诊断与格式化
        md, status = detect_fault(dist_val)
        local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        print(f"\n>>> [设备: {gw_id}] 探头距液面: {dist_val} cm | MD指数: {md} | 状态: {status}")

        # D. 持久化保存
        save_to_csv([local_time, gw_id, dist_val, md, status])

    except Exception as e:
        pass # 屏蔽非自身设备的乱码干扰

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"=== PC 云端监控大脑已启动，守护数据安全 ===")
        client.subscribe(MQTT_TOPIC)

#  5. 守护进程启停逻辑
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, 1883, 60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print(f"\n>>> 收到管理员停止指令。所有数据均已安全落盘至 {CSV_FILE}。系统退出。")
    client.disconnect()