import time
import json
from pymodbus.client import ModbusSerialClient  # 引入 Modbus 串口客户端
import paho.mqtt.client as mqtt
from sm2_crypto import encrypt_data

# --- MQTT 与加密配置保持不变 ---
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "3DPrinter/monitor/gateway/data_814723"

# --- 1. 配置 Modbus RTU 客户端 (针对 DFR0824 扩展板) ---
# 注意：波特率(baudrate)等参数必须与你的工业设备说明书完全一致！
modbus_client = ModbusSerialClient(
    port='/dev/ttyS0',  # 树莓派默认串口
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1  # 读不到数据 1 秒后超时
)


#  (on_connect 回调和 MQTT 客户端初始化代码保持不变)

def run_gateway():
    print("=== 基于树莓派的加密网关已启动 (实战硬件版) ===")

    # 尝试打开串口
    if not modbus_client.connect():
        print("🚨 致命错误：无法打开 RS485 串口，请检查硬件连接或权限！")
        return

    try:
        while True:
            # --- A. 协议转换第一步：读取底层 Modbus RTU 数据 ---
            # 假设你的设备站号(slave)是 1，数据存在寄存器地址 0 中
            try:
                response = modbus_client.read_holding_registers(address=0, count=1, slave=1)

                if response.isError():
                    print("⚠️ Modbus 读取失败：设备无响应或地址错误")
                    real_distance = -1.0  # 用 -1 代表故障
                else:
                    # 拿到真实的寄存器数值 (假设设备返回的是扩大了 10 倍的整数)
                    raw_value = response.registers[0]
                    real_distance = raw_value / 10.0  # 恢复真实的物理量
                    print(f"✅ 成功从 RS485 读取到真实物理量: {real_distance}")
            except Exception as e:
                print(f"⚠️ 串口通信异常: {e}")
                real_distance = -1.0

            # --- B. 协议转换第二步：封装为互联网 JSON 格式 ---
            payload = {
                "gw_id": "Gateway_RS485",
                "distance": real_distance,
                "timestamp": int(time.time())
            }
            json_str = json.dumps(payload)

            # --- C. 国密加固与 MQTT 传输 (保持不变) ---
            if real_distance != -1.0:  # 只有读到正确数据才加密发送
                encrypted_hex = encrypt_data(json_str)
                client.publish(MQTT_TOPIC, encrypted_hex)
                print(f">>> [已安全上传云端] 密文: {encrypted_hex[:20]}...")

            print("-" * 40)
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n>>> 收到停止指令...")
    finally:
        # 安全退出：关闭串口和网络
        modbus_client.close()
        client.loop_stop()
        client.disconnect()
        print(">>> 网关已安全断开所有物理与网络连接。")


if __name__ == "__main__":
    run_gateway()
