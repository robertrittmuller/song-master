import os
import sys
import base64
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _is_truthy_env(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _is_real_langfuse_key(value: Optional[str]) -> bool:
    if not value:
        return False
    trimmed = value.strip()
    if not trimmed:
        return False
    lowered = trimmed.lower()
    return not lowered.startswith("your_langfuse_")


_LANGFUSE_ACTIVE = (
    _is_truthy_env(os.getenv("LANGFUSE_ENABLED"))
    and _is_real_langfuse_key(os.getenv("LANGFUSE_PUBLIC_KEY"))
    and _is_real_langfuse_key(os.getenv("LANGFUSE_SECRET_KEY"))
)

if _LANGFUSE_ACTIVE:
    from langfuse.openai import OpenAI
else:
    from openai import OpenAI

base_prompt = "You are an AI that generates album cover art based on textual descriptions in portrait aspect ratio. Create a visually striking and unique album cover art image based on the following description: "

def generate_album_art_image(prompt: str, output_file: str) -> None:
    """
    Generate album cover art based on a textual prompt and save to a file.

    Args:
        prompt: The description for the album cover art.
        output_file: The path where the image will be saved.

    Raises:
        ValueError: If OPENROUTER_API_KEY is missing.
        RuntimeError: If no image is returned from the API.
    """
    # Load API key from environment variable
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY environment variable")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # Request image
    response = client.chat.completions.create(
        model="google/gemini-3-pro-image-preview",
        messages=[{"role": "user", "content": base_prompt + prompt}],
        extra_body={"modalities": ["image", "text"]},
    )

    message = response.choices[0].message

    if not message.images:
        raise RuntimeError("No image returned from the API")

    # Extract base64 image
    image_data_url = message.images[0]["image_url"]["url"]
    base64_data = image_data_url.split(",", 1)[1]  # strip "data:image/jpeg;base64,"

    # Decode + write to file
    with open(output_file, "wb") as f:
        f.write(base64.b64decode(base64_data))

def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_image.py \"<prompt>\" <output_file>")
        sys.exit(1)

    prompt = sys.argv[1]
    output_file = sys.argv[2]

    try:
        generate_album_art_image(prompt, output_file)
        print(f"Image saved to {output_file}")
    except Exception as e:
        print(f"Error generating album art: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
