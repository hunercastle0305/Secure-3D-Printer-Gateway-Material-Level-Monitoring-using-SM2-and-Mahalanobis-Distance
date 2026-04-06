from gmssl import sm2

# 统一密钥对
PK = '040AE4C7798AA0F119471BEE11825124730D0BD8221145012675272421D807A0F156A0D2A70A3D079D128B2FA8BD433C6C068C8D803DFF79792A519A55171B1B65'
SK = '128B2FA8BD433C6C068C8D803DFF79792A519A55171B1B650C2BDB7C924D0409'

# 测试加密
crypt = sm2.CryptSM2(public_key=PK, private_key=SK, mode=1)
test_msg = '{"test": "ok"}'.encode('utf-8')
enc = crypt.encrypt(test_msg)

# 测试解密
dec = crypt.decrypt(enc)
if dec.decode('utf-8') == '{"test": "ok"}':
    print(">>> 自测成功：PC端加解密环境正常！")
else:
    print(">>> 自测失败：加解密逻辑不一致。")