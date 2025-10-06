"""Natural language intent parsing tool."""

from typing import List

try:  # pragma: no cover - optional heavy dependency
    import spacy  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback when spaCy unavailable
    spacy = None  # type: ignore[assignment]
from pydantic import BaseModel, Field

from ..logging import build_logger
from ..models import ToolOutput


class ParsedIntent(BaseModel):
    goal: str = Field(..., description="Formalized goal extracted from natural language input.")
    entities: List[str] = Field(default_factory=list, description="Named entities identified in the command.")
    confidence: float = Field(..., description="Parser confidence score between 0 and 1.")


class NLIParserTool:
    """Wrapper around spaCy for intent parsing with custom entity rules."""

    def __init__(self, model: str = "en_core_web_sm") -> None:
        self._logger = build_logger("NLIParserTool")
        if spacy is None:
            self._nlp = None
        else:
            self._nlp = spacy.load(model)
            self._ensure_entity_rules()

    def _ensure_entity_rules(self) -> None:
        if self._nlp is None:
            return
        ruler = self._nlp.add_pipe("entity_ruler", before="ner")
        ruler.add_patterns(
            [
                {"label": "DEVICE_ROLE", "pattern": "core router"},
                {"label": "COMPLIANCE", "pattern": "PCI-DSS"},
                {"label": "SERVICE", "pattern": "video conferencing"},
            ]
        )

    def parse_intent(self, text: str) -> ToolOutput:
        if self._nlp is None:
            tokens = [token for token in text.split() if token.isalpha()]
            entities = [token for token in tokens if token.lower() in {"router", "switch", "firewall"}]
            confidence = min(1.0, 0.5 + 0.05 * len(entities))
        else:
            doc = self._nlp(text)
            entities = [ent.text for ent in doc.ents]
            confidence = min(1.0, 0.7 + 0.05 * len(entities))
        goal = text.strip()
        self._logger.info("parsed_intent", text=text, entities=entities, confidence=confidence)
        return ToolOutput.ok(ParsedIntent(goal=goal, entities=entities, confidence=confidence))
