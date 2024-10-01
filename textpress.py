import sys
import json5
import ell
import re
import logging
import yaml
from colorama import init, Fore, Style
import os
import subprocess
import esprima
import json

init(autoreset=True)  # Initialize colorama

# Configure logging
logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize ell
ell.init(store='./logdir')

def get_model_choice():
    prompt = f"{Fore.YELLOW}Choose AI model:{Fore.WHITE}\n"
    prompt += f"1. Claude (default)\n2. ChatGPT\n3. Llama (local)\n"
    prompt += f"Enter choice (1, 2, or 3): "
    
    while True:
        choice = input(prompt).strip()
        if choice in ["", "1"]:
            return "claude-3-5-sonnet-20240620"
        elif choice == "2":
            return "chatgpt-4o-latest"
        elif choice == "3":
            return "llama3.2"
        else:
            print(f"{Fore.RED}Invalid choice. Please enter 1, 2, 3, or press Enter for default.{Fore.WHITE}")

def get_creativity_level():
    prompt = f"{Fore.YELLOW}Enter creativity level (1-5, default 2):\n"
    prompt += f"{Fore.LIGHTBLUE_EX}Higher levels increase variability but may reduce consistency. 🎨\n"
    prompt += f"{Fore.WHITE}Creativity level: "
    
    while True:
        choice = input(prompt).strip()
        if choice == "":
            return 2
        try:
            level = int(choice)
            if 1 <= level <= 5:
                return level
            else:
                print(f"{Fore.RED}Invalid choice. Please enter a number between 1 and 5, or press Enter for default.{Fore.WHITE}")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a number between 1 and 5, or press Enter for default.{Fore.WHITE}")

def get_temperature(creativity_level):
    temperature_map = {1: 0.0, 2: 0.2, 3: 0.5, 4: 0.8, 5: 1.0}
    return temperature_map[creativity_level]

def ai_completion(prompt, model, max_tokens=1000, temperature=0.2):
    logging.debug(f"Sending request to AI model: {model}")
    try:
        if model == "llama3.2":
            result = llama_local_completion(prompt, max_tokens, temperature)
        else:
            @ell.simple(model=model, max_tokens=max_tokens, temperature=temperature)
            def ell_completion(p):
                return p
            result = ell_completion(prompt)
        logging.debug(f"AI response received. Length: {len(result)}")
        return result
    except Exception as e:
        logging.error(f"Error in AI completion: {str(e)}")
        raise

def llama_local_completion(prompt, max_tokens=1000, temperature=0.2):
    try:
        command = ["ollama", "run", "llama3.2", "-t", str(temperature), prompt]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running Llama 3.2 locally: {e}")
        raise

def format_detector(file_path, model):
    # Read the content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Determine format based on file extension
    _, file_extension = os.path.splitext(file_path)
    extension_map = {
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.ts': 'TypeScript',
    }
    if file_extension in extension_map:
        detected_format = extension_map[file_extension]
    else:
        # Fallback to AI-based detection or default to PlainText
        detected_format = 'PlainText'

    return detected_format, content

def generate_structure_prompt(format_name, content):
    prompt = f"""Analyze the following {format_name} content and describe its structure. 
    Focus on the overall organization, key elements, and any recurring patterns. 
    Do not provide any Python code in your response.
    
    Content:
    {content[:200000]}
    
    MUST FOLLOW THIS STRICT INSTRUCTION: No comments or explanations. No intro. No nothing. Just the structure that python coder can understand.
    
    Structural analysis:
    """
    return prompt

def compress_string(original: str, format_name: str, expert_field: str, style_guide: str, use_emojis: bool, model: str, temperature: float):
    # Unescape the original string
    unescaped_original = bytes(original, "utf-8").decode("unicode_escape")

    # Remove surrounding quotes if present
    if (unescaped_original.startswith("'") and unescaped_original.endswith("'")) or \
       (unescaped_original.startswith('"') and unescaped_original.endswith('"')):
        unescaped_original = unescaped_original[1:-1]

    emoji_instruction = "Include relevant emojis in the output." if use_emojis else "Do not use emojis."
    prompt = f"""You are an expert at making text more concise without changing its meaning. Don't reword, don't improve. Think hard and find ways to combine and shorten the text. Fix grammar. No talk; just go. `interactive=false`
    Compress the given text content from a {format_name} file. Follow these guidelines:
    1. Maintain the original meaning while making the text significantly more concise.
    2. The compressed string MUST be shorter than the original.
    3. Use language appropriate for an expert in {expert_field}.
    4. {emoji_instruction}
    5. {style_guide}
    6. Return ONLY the compressed string.
    7. Do NOT wrap output in quotes.

    Original string: {unescaped_original}

    Compressed string:"""

    @ell.simple(model=model, max_tokens=1000, temperature=temperature)
    def ell_compress(p):
        return p

    compressed_result = ell_compress(prompt).strip()

    # Re-add quotes if they were present in the original
    if original.startswith("'") and original.endswith("'"):
        compressed_result = f"'{compressed_result}'"
    elif original.startswith('"') and original.endswith('"'):
        compressed_result = f'"{compressed_result}"'

    return compressed_result

import time
from itertools import cycle

def compress_strings(strings, format_name, expert_field, style_guide, use_emojis, model, max_attempts, temperature):
    compressed_strings = []
    compression_attempts = []
    spinner = cycle(['-', '\\', '|', '/'])
    
    for i, string in enumerate(strings):
        attempts = 1
        shortest_compressed = string
        current_string = string
        
        print(f"\n{Fore.CYAN}Compressing string {i+1}/{len(strings)}:")
        print(f"{Fore.YELLOW}Before: {string[:100]}{'...' if len(string) > 100 else ''}")
        
        while attempts <= max_attempts:
            print(f"\r{Fore.WHITE}Attempt {attempts}/{max_attempts} {next(spinner)}", end='', flush=True)
            
            if model == "llama3.2":
                prompt = compress_string(
                    current_string, format_name, expert_field, style_guide, use_emojis, model
                )
                compressed = llama_local_completion(prompt, 1000, temperature)
            else:
                compressed = compress_string(
                    current_string, format_name, expert_field, style_guide, use_emojis, model, temperature
                )
            compressed = compressed.strip()
            
            if len(compressed) < len(shortest_compressed):
                shortest_compressed = compressed
                current_string = compressed
            else:
                break
            attempts += 1
            time.sleep(0.017)  # Add a small delay for visual effect
        
        print(f"\r{Fore.GREEN}Compressed in {attempts} attempt(s):")
        print(f"{Fore.MAGENTA}After:  {shortest_compressed[:100]}{'...' if len(shortest_compressed) > 100 else ''}")
        print(f"{Fore.BLUE}Length: {len(string)} → {len(shortest_compressed)} ({(1 - len(shortest_compressed) / len(string)) * 100:.2f}% reduction)")
        
        compressed_strings.append(shortest_compressed)
        compression_attempts.append(attempts)
    
    return compressed_strings, compression_attempts

def calculate_stats(original_content, compressed_content, compression_attempts):
    original_size = len(original_content.encode('utf-8'))
    compressed_size = len(compressed_content.encode('utf-8'))
    compression_ratio = (1 - compressed_size / original_size) * 100

    original_strings = re.findall(r'"([^"]*)"', original_content)
    compressed_strings = re.findall(r'"([^"]*)"', compressed_content)

    avg_original_len = sum(len(s) for s in original_strings) / len(original_strings) if original_strings else 0
    avg_compressed_len = sum(len(s) for s in compressed_strings) / len(compressed_strings) if compressed_strings else 0
    avg_compression_attempts = sum(compression_attempts) / len(compression_attempts) if compression_attempts else 0

    return {
        'original_size': original_size,
        'compressed_size': compressed_size,
        'compression_ratio': compression_ratio,
        'avg_original_len': avg_original_len,
        'avg_compressed_len': avg_compressed_len,
        'avg_compression_attempts': avg_compression_attempts
    }

def display_stats(stats):
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Compression Statistics:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*40}")
    print(f"{Fore.GREEN}Original file size:    {stats['original_size']:,} bytes")
    print(f"{Fore.GREEN}Compressed file size:  {stats['compressed_size']:,} bytes")
    print(f"{Fore.MAGENTA}Compression ratio:     {stats['compression_ratio']:.2f}%")
    print(f"{Fore.BLUE}Avg original length:   {stats['avg_original_len']:.2f} characters")
    print(f"{Fore.BLUE}Avg compressed length: {stats['avg_compressed_len']:.2f} characters")
    print(f"{Fore.BLUE}Avg compression attempts: {stats['avg_compression_attempts']:.2f}")
    print(f"{Fore.YELLOW}{'='*40}")

def replace_strings_in_content_by_positions(content, positions, original_strings, compressed_strings):
    new_content = content
    offset = 0  # Offset due to length changes

    for (start, end), original, compressed in zip(positions, original_strings, compressed_strings):
        adjusted_start = start + offset
        adjusted_end = end + offset

        # Extract the original string (including quotes)
        original_string_with_quotes = new_content[adjusted_start:adjusted_end]
        quote_char = original_string_with_quotes[0]  # Either ' or "

        # Unescape the compressed string
        compressed_unescaped = bytes(compressed, "utf-8").decode("unicode_escape")

        # Remove surrounding quotes if present in the compressed string
        if (compressed_unescaped.startswith("'") and compressed_unescaped.endswith("'")) or \
           (compressed_unescaped.startswith('"') and compressed_unescaped.endswith('"')):
            compressed_unescaped = compressed_unescaped[1:-1]

        # Escape only necessary characters for JavaScript
        compressed_escaped = compressed_unescaped.replace('\\', '\\\\').replace(quote_char, f'\\{quote_char}')

        # Reconstruct the string with the original quote character
        replaced_string = f"{quote_char}{compressed_escaped}{quote_char}"

        # Replace in the content
        new_content = new_content[:adjusted_start] + replaced_string + new_content[adjusted_end:]
        offset += len(replaced_string) - (adjusted_end - adjusted_start)

    return new_content

def extract_strings_with_positions(content, format_name):
    # Extract all strings and positions
    if format_name == 'JavaScript':
        strings, positions = extract_strings_from_javascript(content)
    elif format_name == 'JSON':
        strings, positions = extract_strings_from_json(content)
    elif format_name == 'YAML':
        strings, positions = extract_strings_from_yaml(content)
    else:
        strings, positions = extract_strings_with_regex(content)
    
    # Store the original strings and positions
    original_strings = strings.copy()
    original_positions = positions.copy()
    
    # Filter out strings that are under 12 characters or only one word
    filtered_strings = []
    filtered_positions = []
    for string, position in zip(strings, positions):
        if is_sentence(string):
            filtered_strings.append(string)
            filtered_positions.append(position)
    return original_strings, original_positions, filtered_strings, filtered_positions

def extract_strings_with_regex(content):
    # Fallback function using regex
    string_matches = list(re.finditer(r'(["\'])(?:(?=(\\?))\2.)*?\1', content))
    strings = []
    positions = []
    for match in string_matches:
        full_match = match.group(0)
        quote_char = full_match[0]
        string_content = full_match[1:-1]
        if not string_content.isdigit():
            strings.append(string_content)
            positions.append(match.span())
    return strings, positions

def extract_strings_from_javascript(content):
    strings = []
    positions = []
    tokens = esprima.tokenize(content, loc=True, range=True)
    for token in tokens:
        if token.type == 'String':
            # Preserve the original string including quotes
            value = token.value
            start = token.range[0]
            end = token.range[1]
            strings.append(value)
            positions.append((start, end))
    return strings, positions

def get_absolute_position(content, line_number, column_number):
    lines = content.split('\n')
    position = sum(len(lines[i]) + 1 for i in range(line_number)) + column_number
    return position

def is_sentence(text):
    # Returns True if text is at least 12 characters and contains more than one word
    return len(text) >= 12 and len(text.strip().split()) > 1

def extract_strings_from_json(content):
    strings = []
    positions = []
    try:
        data = json.loads(content)
        for string, pos in find_strings_in_json(data, content):
            if is_sentence(string):
                strings.append(string)
                positions.append(pos)
    except json.JSONDecodeError:
        # Fallback to regex if JSON is invalid
        return extract_strings_with_regex(content)
    return strings, positions

def extract_strings_from_yaml(content):
    strings = []
    positions = []
    try:
        data = yaml.safe_load(content)
        for string, pos in find_strings_in_yaml(data, content):
            if is_sentence(string):
                strings.append(string)
                positions.append(pos)
    except yaml.YAMLError:
        # Fallback to regex if YAML is invalid
        return extract_strings_with_regex(content)
    return strings, positions

def find_strings_in_json(data, content, path=""):
    if isinstance(data, str):
        start = content.index(json.dumps(data), 0)
        end = start + len(json.dumps(data))
        yield data, (start, end)
    elif isinstance(data, dict):
        for key, value in data.items():
            yield from find_strings_in_json(value, content, f"{path}.{key}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            yield from find_strings_in_json(item, content, f"{path}[{i}]")

def find_strings_in_yaml(data, content, path=""):
    if isinstance(data, str):
        start = content.index(data, 0)
        end = start + len(data)
        yield data, (start, end)
    elif isinstance(data, dict):
        for key, value in data.items():
            yield from find_strings_in_yaml(value, content, f"{path}.{key}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            yield from find_strings_in_yaml(item, content, f"{path}[{i}]")

def main():
    logging.info("Starting AI Text Copy Compressor")
    print(f"{Fore.CYAN}{Style.BRIGHT}Welcome to the AI Text Copy Compressor! 🧠✨{Style.RESET_ALL}")
    
    # Check for correct number of arguments
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"{Fore.RED}Error: Please provide input file path and optionally output file path.")
        print(f"{Fore.YELLOW}Usage: python psycho.py <input_file> [output_file]")
        sys.exit(1)
    
    # Obtain input file path
    input_file = sys.argv[1]
    
    # Determine output file path
    if len(sys.argv) == 3:
        output_file = sys.argv[2]
    else:
        # If no output file is specified, use _output.originalextension format
        input_name, input_ext = os.path.splitext(input_file)
        output_file = f"{input_name}_output{input_ext}"
    
    logging.info(f"Input file: {input_file}")
    logging.info(f"Output file: {output_file}")

    # Get model choice
    model = get_model_choice()
    logging.info(f"Using model: {model}")

    # Get creativity level
    creativity_level = get_creativity_level()
    temperature = get_temperature(creativity_level)
    logging.info(f"Creativity level: {creativity_level}, Temperature: {temperature}")
    print(f"{Fore.MAGENTA}Creativity level set to: {creativity_level} (Temperature: {temperature}) 🎨")

    # Prompt for compression level
    compression_level_prompt = (
        f"{Fore.YELLOW}Enter compression level (1-5, default 3):\n"
        f"{Fore.LIGHTBLUE_EX}This defines the number of attempts to compress each line. "
        f"Higher levels may result in more aggressive compression but may take longer. 🚀\n"
        f"{Fore.WHITE}Compression level: "
    )
    compression_level_input = input(compression_level_prompt).strip()
    if compression_level_input == '':
        compression_level = 3
    else:
        try:
            compression_level = int(compression_level_input)
            if compression_level < 1 or compression_level > 5:
                print(f"{Fore.RED}Invalid compression level. Must be between 1 and 5. Using default level 3.")
                compression_level = 3
        except ValueError:
            print(f"{Fore.RED}Invalid input. Using default compression level 3.")
            compression_level = 3
    print(f"{Fore.MAGENTA}Compression level set to: {compression_level} 🔥")

    # Detect format and structure
    logging.info("Detecting file format and structure")
    format_name, content = format_detector(input_file, model)
    logging.info(f"Detected format: {format_name}")

    # Analyze structure if applicable
    if format_name in ['JSON', 'YAML']:
        logging.info("Analyzing file structure")
        structure_prompt = generate_structure_prompt(format_name, content)
        structure = ai_completion(structure_prompt, model, temperature=temperature)
        logging.debug(f"Structure analysis result: {structure[:100]}...")

    # Prompt for expert field
    expert_prompt = (
        f"{Fore.YELLOW}Enter the field of expertise for the text (e.g., psychology, medicine, law):\n"
        f"{Fore.LIGHTBLUE_EX}This helps tailor the compression to the specific domain. 🎓\n"
        f"{Fore.WHITE}Enter the field: "
    )
    expert_field = input(expert_prompt).strip()
    print(f"{Fore.MAGENTA}Selected field: {expert_field} 📚")

    # Prompt for optional style guide
    style_prompt = (
        f"{Fore.YELLOW}Enter any additional style guidelines (optional):\n"
        f"{Fore.LIGHTBLUE_EX}E.g., 'formal', 'casual', 'technical', 'use metaphors'. Press Enter to skip. 🎨\n"
        f"{Fore.WHITE}Style guide: "
    )
    style_guide = input(style_prompt).strip()
    if style_guide:
        print(f"{Fore.MAGENTA}Style guide: {style_guide} 🖋️")
    else:
        print(f"{Fore.MAGENTA}No additional style guide provided 🖋️")

    # Prompt for emoji usage
    emoji_prompt = (
        f"{Fore.YELLOW}Want emojis in compressed text? (y/N):\n"
        f"{Fore.LIGHTBLUE_EX}Emojis can add visual appeal but may affect meaning. 🤔\n"
        f"{Fore.WHITE}Enter your choice: "
    )
    use_emojis = input(emoji_prompt).strip().lower() == 'y'
    print(f"{Fore.MAGENTA}Emoji usage: {'Enabled 😊' if use_emojis else 'Disabled 🚫'}")

    # Extract strings and positions
    logging.info("Extracting strings")
    original_strings, original_positions, strings_to_compress, positions_to_compress = extract_strings_with_positions(
        content=content,
        format_name=format_name
    )
    num_strings = len(original_strings)
    num_strings_to_compress = len(strings_to_compress)
    print(f"{Fore.GREEN}Found {num_strings} strings in the file.")
    print(f"{Fore.CYAN}{num_strings_to_compress} strings will be compressed based on the criteria.")

    # Compress strings
    logging.info("Compressing content")
    compressed_strings, compression_attempts = compress_strings(
        strings=strings_to_compress,
        format_name=format_name,
        expert_field=expert_field,
        style_guide=style_guide,
        use_emojis=use_emojis,
        model=model,
        max_attempts=compression_level,
        temperature=temperature
    )

    # Replace compressed strings in content
    logging.info("Replacing strings in content")
    modified_content = replace_strings_in_content_by_positions(
        content=content,
        positions=positions_to_compress,
        original_strings=strings_to_compress,
        compressed_strings=compressed_strings
    )

    # Write the compressed content to the output file
    logging.info(f"Writing compressed content to output file: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)

    # Calculate and display statistics
    stats = calculate_stats(content, modified_content, compression_attempts)
    display_stats(stats)

    # Display before and after samples
    logging.info("Displaying sample comparison")
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Sample Comparison:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*40}") 
    print(f"{Fore.GREEN}Before (first 100 characters):")
    print(content[:100])
    print(f"\n{Fore.MAGENTA}After (first 100 characters):")
    print(modified_content[:100])
    print(f"{Fore.YELLOW}{'='*40}")

    logging.info("AI Text Copy Compressor completed successfully")

if __name__ == '__main__':
    main()