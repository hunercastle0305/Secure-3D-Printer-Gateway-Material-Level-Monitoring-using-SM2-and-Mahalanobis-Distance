from gmssl import sm2, func

# 1. 产生一对该库认可的原始密钥
sm2_crypt = sm2.CryptSM2(public_key='', private_key='')
random_hex_str = func.random_hex(64)
# 生成私钥和公钥
sk = random_hex_str
pk = sm2_crypt._kg(int(sk, 16), sm2.default_ecc_table['g'])

print(f"你的专属私钥 (SK): {sk}")
print(f"你的专属公钥 (PK): {pk}")

# 2. 现场测试这对密钥是否能用
test_crypt = sm2.CryptSM2(public_key=pk, private_key=sk, mode=1)
enc = test_crypt.encrypt(b"hello")
dec = test_crypt.decrypt(enc)

if dec == b"hello":
    print("\n>>> 恭喜！这对密钥在你的环境中完全正常，请立即替换到代码中。")
else:
    print("\n>>> 警告：mode=1 失败，尝试将代码中的 mode 改为 0 再试一次。")