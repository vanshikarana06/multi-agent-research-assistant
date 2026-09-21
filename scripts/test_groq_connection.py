from groq import Groq

from app.core.config import settings


def main() -> None:
    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Reply with exactly one word : 'connected'."}],
    )
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
