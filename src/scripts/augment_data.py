import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Path configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

try:
    from openai import OpenAI
except ImportError:
    print("Error: 'openai' package is not installed. Please install it using 'pip install openai'.")
    sys.exit(1)

IDIOMS_FILE = PROJECT_ROOT / "data" / "reference" / "idioms_en_tr.json"

# A list of some common English idioms to feed the generator for expansion
IDIOMS_TO_EXPAND = [
    "break a leg", "burn the midnight oil", "call it a day", "cut corners",
    "cry over spilled milk", "easy does it", "get out of hand", "hang in there",
    "let the cat out of the bag", "miss the boat", "no pain no gain",
    "on the ball", "pull someone's leg", "under the weather", "wrap your head around",
    "a penny for your thoughts", "actions speak louder than words", "back to the drawing board",
    "bite off more than you can chew", "burn bridges", "don't count your chickens before they hatch",
    "draw the line", "every cloud has a silver lining", "go the extra mile",
    "haste makes waste", "it takes two to tango", "kill two birds with one stone",
    "leave no stone unturned", "make a long story short", "once in a blue moon",
    "picture paints a thousand words", "speak of the devil", "steal someone's thunder",
    "take it with a grain of salt", "the elephant in the room", "through thick and thin",
    "throw caution to the wind", "whole nine yards", "wild goose chase",
    "cost an arm and a leg", "let sleeping dogs lie", "cross that bridge when we come to it"
]

def load_existing_idioms():
    if IDIOMS_FILE.exists():
        try:
            with open(IDIOMS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not read existing idioms file: {e}. Starting fresh.")
    return []

def save_idioms(idioms):
    IDIOMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(IDIOMS_FILE, "w", encoding="utf-8") as f:
        json.dump(idioms, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved {len(idioms)} idioms to {IDIOMS_FILE}")

def generate_idiom_data(client, model, existing_idiom_names):
    # Filter out idioms we already have
    remaining_idioms = [i for i in IDIOMS_TO_EXPAND if i.lower() not in existing_idiom_names]
    
    if not remaining_idioms:
        print("All predefined idioms are already in the database!")
        return []
    
    # Process in batches of 10 to manage prompt size and stability
    batch_size = 10
    batch = remaining_idioms[:batch_size]
    
    print(f"Generating data for batch: {', '.join(batch)}...")
    
    prompt = f"""
You are a professional literary translator specializing in English to Turkish translation.
For the following English idioms, provide:
1. Meaning: Clear explanation of the idiom in English.
2. Turkish Equivalent: Natural Turkish equivalents (deyimler, atasözleri veya edebi ifadeler). Provide 2-3 variations separated by slashes.
3. Context: In which situations this idiom is used, written in Turkish.

Idioms to process:
{json.dumps(batch, indent=2)}

You must output a valid JSON array of objects. Do not wrap the JSON in ```json or any other formatting, output raw JSON. Each object must have these exact keys:
- "idiom": The exact English idiom string from the list.
- "meaning": The English meaning.
- "turkish_equivalent": The Turkish equivalents (separated by /).
- "context": The usage context in Turkish.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful translation data engineer. Output raw JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        
        # Clean up any potential markdown fences just in case
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            
        new_idioms = json.loads(content)
        return new_idioms
    except Exception as e:
        print(f"Error during generation: {e}")
        return []

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please copy .env.example to .env and insert your API key.")
        sys.exit(1)
        
    model = os.getenv("DEFAULT_MINI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)
    
    existing_idioms = load_existing_idioms()
    existing_idiom_names = {i["idiom"].lower() for i in existing_idioms}
    print(f"Loaded {len(existing_idioms)} existing idioms.")
    
    new_idioms = generate_idiom_data(client, model, existing_idiom_names)
    
    if new_idioms:
        # Merge and save
        merged = existing_idioms + new_idioms
        save_idioms(merged)
    else:
        print("No new idioms were generated.")

if __name__ == "__main__":
    main()
