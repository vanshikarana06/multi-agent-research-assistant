from langgraph.checkpoint.redis import RedisSaver
from langgraph.checkpoint.redis.jsonplus_redis import JsonPlusRedisSerializer

from app.models.finding import Finding, Source
from app.models.plan import ResearchPlan, SubQuestion
from app.models.report import Citation, ReportSection, ResearchReport

_STATE_MODELS = (
    Finding,
    Source,
    ResearchPlan,
    SubQuestion,
    ResearchReport,
    ReportSection,
    Citation,
)

ALLOWED_JSON_MODULES = [
    tuple(f"{cls.__module__}.{cls.__qualname__}".split(".")) for cls in _STATE_MODELS
]


def make_checkpointer(redis_url: str) -> RedisSaver:
    saver = RedisSaver(redis_url=redis_url)
    saver.serde = JsonPlusRedisSerializer(allowed_json_modules=ALLOWED_JSON_MODULES)
    saver.setup()
    return saver
