#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: 'pyyaml' is required. Install it using: pip install pyyaml")
    sys.exit(1)


# Custom Dumper to format multi-line responses with YAML standard block scalar (>)
class CleanYAMLDumper(yaml.SafeDumper):
    pass

def represent_multiline_str(dumper, data):
    if '\n' in data:
        # Uses > block scalar format for multi-line response strings
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='>')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

CleanYAMLDumper.add_representer(str, represent_multiline_str)


def load_yaml(file_path: Path) -> dict:
    if not file_path.exists():
        print(f"❌ File '{file_path}' not found.")
        sys.exit(1)
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if "topic_areas" not in data or not isinstance(data["topic_areas"], list):
        data["topic_areas"] = []
        
    return data


def save_yaml(file_path: Path, data: dict):
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            Dumper=CleanYAMLDumper,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True
        )
    print(f"\n✅ Saved updates to '{file_path}'.\n")


def display_topics(topics: list):
    print("\n--- Topic Areas ---")
    if not topics:
        print(" (No topic areas found)")
        return
    for idx, topic in enumerate(topics, 1):
        title = topic.get("title", topic.get("name", "Untitled Topic"))
        q_count = len(topic.get("questions", []))
        print(f"  {idx}) {title} ({q_count} questions)")
    print("-------------------")


def prompt_multiline_input(prompt_text: str) -> str:
    print(f"\n{prompt_text} (Enter a single period '.' on a blank line when finished):")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == ".":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def add_section(data: dict, file_path: Path):
    topics = data["topic_areas"]
    display_topics(topics)
    
    print("\n[Add New Topic Section]")
    print("Position choices:")
    print(" • Enter a number (1, 2, etc.) to insert BEFORE that existing section.")
    print(" • Press Enter or choose a number outside the list to append to the END.")
    
    pos_input = input("Target position: ").strip()
    
    name = input("Enter unique topic internal name (e.g., 'understanding_addiction'): ").strip()
    title = input("Enter display title (e.g., 'Understanding Addiction'): ").strip()
    
    new_topic = {
        "name": name,
        "title": title,
        "questions": []
    }
    
    if pos_input.isdigit():
        pos = int(pos_input) - 1
        if 0 <= pos < len(topics):
            topics.insert(pos, new_topic)
        else:
            topics.append(new_topic)
    else:
        topics.append(new_topic)
        
    save_yaml(file_path, data)


def add_question(data: dict, file_path: Path):
    topics = data["topic_areas"]
    if not topics:
        print("\n❌ No topics exist yet. Please add a section first.")
        return

    display_topics(topics)
    
    topic_idx_input = input("\nSelect the Topic number for this question: ").strip()
    if not topic_idx_input.isdigit() or not (1 <= int(topic_idx_input) <= len(topics)):
        print("❌ Invalid topic selection.")
        return
        
    target_topic = topics[int(topic_idx_input) - 1]
    questions = target_topic.get("questions", [])
    
    print(f"\n--- Questions in '{target_topic.get('title')}' ---")
    if not questions:
        print(" (No questions currently in this topic)")
    else:
        for idx, q in enumerate(questions, 1):
            print(f"  {idx}) {q.get('question')}")
    print("--------------------------------------------------")
    
    print("\nPosition choices:")
    print(" • Enter a number to insert BEFORE that question.")
    print(" • Press Enter to append to the END of this group.")
    
    q_pos_input = input("Target position: ").strip()
    
    q_text = input("\nEnter the Question: ").strip()
    if not q_text:
        print("❌ Question cannot be empty.")
        return
        
    r_text = prompt_multiline_input("Enter the Response text")
    
    new_q = {
        "question": q_text,
        "response": r_text
    }
    
    if q_pos_input.isdigit():
        pos = int(q_pos_input) - 1
        if 0 <= pos < len(questions):
            questions.insert(pos, new_q)
        else:
            questions.append(new_q)
    else:
        questions.append(new_q)
        
    target_topic["questions"] = questions
    save_yaml(file_path, data)


def main():
    parser = argparse.ArgumentParser(description="Interactive FAQ YAML Editor")
    parser.add_argument("file", type=Path, help="Path to the FAQ YAML file")
    args = parser.parse_args()

    file_path = args.file
    data = load_yaml(file_path)

    while True:
        display_topics(data["topic_areas"])
        print("\nOptions:")
        print(" [s] Add a new Section/Topic")
        print(" [a] Add a Question to a topic")
        print(" [q] Quit")
        
        choice = input("\nSelect action (s/a/q): ").strip().lower()
        
        if choice == 's':
            add_section(data, file_path)
        elif choice == 'a':
            add_question(data, file_path)
        elif choice == 'q':
            print("Exiting tool.")
            break
        else:
            print("❌ Invalid command. Please type 's', 'a', or 'q'.")


if __name__ == "__main__":
    main()
