import argparse
import json
from tqdm import tqdm

import datasets
import transformers


def preprocess(tokenizer, config, example, max_seq_length):
    prompt = example["context"]
    target = example["target"]
    prompt_ids = tokenizer.encode(prompt, max_length=max_seq_length, truncation=True)
    target_ids = tokenizer.encode(
        target,
        max_length=max_seq_length,
        truncation=True,
        add_special_tokens=False)
    input_ids = prompt_ids + target_ids + [config.eos_token_id]
    return {"input_ids": input_ids, "seq_len": len(prompt_ids)}


def read_jsonl(model_name, path, max_seq_length, skip_overlength=False):
    tokenizer = transformers.AutoTokenizer.from_pretrained(f"../../huggingface/{model_name}", trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    config = transformers.AutoConfig.from_pretrained(
        f"../../huggingface/{model_name}", trust_remote_code=True, device_map='auto')
    with open(path, "r") as f:
        for line in tqdm(f.readlines()):
            example = json.loads(line)
            feature = preprocess(tokenizer, config, example, max_seq_length)
            if skip_overlength and len(feature["input_ids"]) > max_seq_length:
                continue
            feature["input_ids"] = feature["input_ids"][:max_seq_length]
            yield feature


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl_path", type=str, default="./datasets/luxun_dataset.jsonl")
    parser.add_argument("--save_path", type=str, default="./datasets/")
    parser.add_argument("--max_seq_length", type=int, default=384)
    parser.add_argument("--skip_overlength", action="store_true", default=False)
    parser.add_argument("--model_name", type=str, default="qwen-2.5-3B-instruct")
    args = parser.parse_args()
    

    print("#> Tokenizing dataset...")
    print("#> Input path: {}".format(args.jsonl_path))
    print("#> Output path: {}".format(args.save_path))
    print("#> Max sequence length: {}".format(args.max_seq_length))
    print("#> Skip overlength: {}".format(args.skip_overlength))

    

    dataset = datasets.Dataset.from_generator(
        lambda: read_jsonl(args.model_name, args.jsonl_path, args.max_seq_length, args.skip_overlength)
    )
    save_path = f'./datasets/{args.model_name}'
    dataset.save_to_disk(save_path)

    print("#> Tokenization finished!", "Total examples:", len(dataset))


if __name__ == "__main__":
    main()
