from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
import threading
import torch
from config import MODEL_PATH

# 自动检测设备
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading model on {device} from {MODEL_PATH}...")

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        device_map="auto",
        # 如果是 CPU，不支持 float16，需根据情况调整
        dtype=torch.float16 if device == "cuda" else torch.float32
    )
except Exception as e:
    print(f"Error loading model: {e}")
    print("请检查 generator.py 中的 MODEL_PATH 路径是否正确。")
    exit(1)

def generate_answer_stream(prompt_messages: list):
    """
    接收标准的消息列表格式：[{"role": "system",...}, {"role": "user",...}]
    """
    
    text = tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=2048)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    streamer = TextIteratorStreamer(
        tokenizer,
        skip_prompt=True,
        skip_special_tokens=True
    )

    generation_kwargs = dict(
        **inputs,
        streamer=streamer,
        max_new_tokens=512,
        do_sample=True,      # 适当采样可以让回答更自然，但设低 temp
        temperature=0.2,     # 低温度保证准确性
        repetition_penalty=1.1,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id
    )

    thread = threading.Thread(
        target=model.generate,
        kwargs=generation_kwargs
    )
    thread.start()

    try:
        for text in streamer:
            yield text
    except Exception as e:
        yield f"生成出错: {str(e)}"