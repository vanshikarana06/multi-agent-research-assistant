import json
from groq import Groq
from app.core.config import settings
from app.models.example import MovieRecommendation


def main() -> None:
    client = Groq(api_key=settings.groq_api_key)
    schema = MovieRecommendation.model_json_schema()
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You recommend one movie . Respond with a JSON object matching"
                    f"this schema : {json.dumps(schema)}"
                ),
            },
            {"role": "user", "content": "Recommend a good sci-fi movie."},
        ],
        response_format={"type": "json_object"},
    )
    print("schema:")
    print(schema)
    raw_content = response.choices[0].message.content
    print("raw model output:")
    print(raw_content)

    movie = MovieRecommendation.model_validate_json(raw_content)
    print("\nValidated pydantic output:")
    print(movie)


if __name__ == "__main__":
    main()
