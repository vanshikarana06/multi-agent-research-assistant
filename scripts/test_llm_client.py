from app.models.example import MovieRecommendation
from app.services.llm_client import LLMClient


def main() -> None:
    client = LLMClient()

    movie = client.generate(
        schema=MovieRecommendation,
        system_prompt="You recommend one movie.",
        user_prompt="Recommend a good sci-fi movie.",
    )

    print(movie)


if __name__ == "__main__":
    main()
