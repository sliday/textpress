# Textpress: AI Text Copy Compressor

Textpress is a Python script that compresses text content within files using AI models. It processes files like JavaScript, JSON, YAML, etc., extracts text strings, and compresses them to be more concise while retaining their original meaning. The script is interactive and allows customization to tailor the compression process to your needs.

![textpress](https://github.com/user-attachments/assets/96579e5d-11cb-4e15-a78d-326f8315265d)

## How It Works

Textpress follows these steps:

1. **File Processing**: "Reads" (using AI) the input file and detects its format (JSON, YAML, JS, etc).
2. **String Extraction**: Extracts text strings suitable for compression. No need to compress parameters' names, for example.
3. **AI Compression**: Uses an AI model to generate compressed versions of the strings while preserving their meaning.
4. **Content Replacement**: Replaces the original strings with the compressed ones in the content.
5. **Output Generation**: Writes the compressed content to an output file.
6. **Statistics Display**: Provides compression statistics and sample comparisons.

## Available Options

- **AI Model Selection**:
  - **Claude** (default)
  - **ChatGPT**
  - **Llama** (for local processing)
- **Creativity Level (1-5)**:
  - Adjusts the AI's creativity and variability.
  - Higher levels increase creativity but may reduce consistency.
- **Compression Level (1-5)**:
  - Defines how aggressively to compress text.
  - Higher levels attempt more aggressive compression.
- **Field of Expertise**:
  - Tailors the compression to use language appropriate for a specific domain (e.g., psychology, medicine).
- **Style Guidelines**:
  - Provide instructions like "formal", "technical", or "use metaphors".
- **Emoji Inclusion**:
  - Choose to include emojis for added expressiveness.

## Usage

1. **Run the script**:

   ```bash
   python textpress.py <input_file> [output_file]
   ```

   - `<input_file>`: Path to the file you want to compress.
   - `[output_file]` (optional): Path for the output file. Defaults to `<input_name>_output<extension>`.

2. **Follow the interactive prompts**:
   - **AI Model**: Choose between available AI models.
   - **Creativity Level**: Enter a value between 1 (least creative) to 5 (most creative).
   - **Compression Level**: Set the aggressiveness of compression attempts.
   - **Field of Expertise**: Specify the domain for tailored language.
   - **Style Guidelines**: (Optional) Add specific style preferences.
   - **Emoji Usage**: Decide whether to include emojis in the compressed text.

3. **Review the Output**:
   - The script processes the file and saves the compressed content to the output file.
   - Displays compression statistics and sample comparisons.

## Example

Running the script with an input JavaScript file (output file name is optional):

```bash
python textpress.py input.js [output.js]
```

- If `output.js` is not provided, the script defaults to `input_output.js`.

**Interactive Prompts Example**:

- Choose AI model: Press Enter to use the default (Claude).
- Enter creativity level (1-5): `3`
- Enter compression level (1-5): `3`
- Enter the field: `psychology`
- Style guide: `formal`
- Want emojis in compressed text? (y/N): `N`

**Result**:

- Processes `input.js` and saves the compressed content in `output.js` (if specified) or `input_output.js` by default.
- Displays compression statistics and sample comparisons in the terminal.

## Installation

1. **Install required packages**:

   ```bash
   pip install -r requirements.txt
   ```

   Alternatively:

   ```bash
   pip install json5 ell colorama pyyaml esprima
   ```

## Star History

<a href="https://star-history.com/#sliday/textpress&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=sliday/textpress&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=sliday/textpress&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=sliday/textpress&type=Date" />
 </picture>
</a>

## Notes

- **AI Model Credentials**:
  - Ensure the `ell` library is configured with necessary credentials.
- **Review Output**:
  - Always review the compressed content to ensure accuracy.
- **Compatibility**:
  - Supports multiple file formats; some complex structures may have limitations.

## License

This project is licensed under the MIT License.
