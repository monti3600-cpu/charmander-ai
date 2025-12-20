def log(tag, msg):
    print(f"[{tag}] {msg}")


def sys(msg): log("🟡 SYS", msg)
def stt(msg): log("🎤 STT", msg)
def gpt(msg): log("🤖 GPT", msg)
