import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SystemPromptTemplate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str
    node_name: str
    description: str
    mode: Literal["ask", "planning", "execution"] = "ask"
    version: Optional[str] = None
    date: Optional[str] = None
    # assign default traits of helpful and friendly
    traits: Optional[str] = Field(
        default="Your core traits are:\n- helpful\n- friendly"
    )
    # for skills, tools and domain knowledge
    # until we assign something, the agent does not have anything there
    skills: Optional[str] = Field(
        default="None - You do not have access to any skills yet."
    )
    tools: Optional[str] = Field(
        default="None - You do not have access to any tools yet."
    )
    domain_knowledge: Optional[str] = Field(
        default="None - You do not have any domain knowledge yet."
    )
    reasoning_steps: Optional[str] = Field(default="")
    workflow: Optional[str] = Field(default="")
    expected_inputs: Optional[str] = Field(default="")
    expected_outputs: Optional[str] = Field(default="")
    response_guidelines: Optional[str] = Field(default="")
    code_style_guidelines: Optional[str] = Field(default="")
    writing_style_guidelines: Optional[str] = Field(default="")
    guardrails: Optional[str] = Field(default="")
    failure_protocol: Optional[str] = Field(default="")

    @staticmethod
    def _has_text(s: str | None) -> bool:
        return bool(s and s.strip())

    def to_markdown(self):
        md = ""
        md += (
            f"# {self.node_name}: SYSTEM PROMPT\n"
            f"\n## PROFILE\n"
            f"- NAME: {self.name}\n"
            f"- ROLE: {self.node_name}\n"
            f"- DESCRIPTION: {self.description}\n"
            f"- MODE: {self.mode.upper()}\n"
        )
        if self._has_text(self.version):
            md += f"- VERSION: {self.version}\n"
        # if the date is provided use that
        # or else, when the markdown is being generated
        # automatically calculate the date and assign that
        if not self._has_text(self.date):
            self.date = datetime.now().strftime("%B %Y")
        md += f"- DATE: {self.date}\n"
        if self._has_text(self.traits):
            md += f"\n## TRAITS\n{self.traits}\n"
        if self._has_text(self.tools):
            md += f"\n## TOOLS\n{self.tools}\n"
        if self._has_text(self.skills):
            md += f"\n## SKILLS\n{self.skills}\n"
        if self._has_text(self.domain_knowledge):
            md += f"\n## DOMAIN KNOWLEDGE\n{self.domain_knowledge}\n"
        if self._has_text(self.reasoning_steps):
            md += f"\n## CHAIN OF THOUGHT\n{self.reasoning_steps}\n"
        if self._has_text(self.workflow):
            md += f"\n## WORKFLOW\n{self.workflow}\n"
        if self._has_text(self.expected_inputs):
            md += f"\n## EXPECTED INPUTS\n{self.expected_inputs}\n"
        if self._has_text(self.expected_outputs):
            md += f"\n## EXPECTED OUTPUTS\n{self.expected_outputs}\n"
        if self._has_text(self.response_guidelines):
            md += f"\n## RESPONSE GUIDELINES\n{self.response_guidelines}\n"
        if self._has_text(self.code_style_guidelines) or self._has_text(
            self.writing_style_guidelines
        ):
            md += "\n## CONTEXTUAL GUIDELINES\n"
            if self._has_text(self.code_style_guidelines):
                md += f"\n### CODE STYLE GUIDELINES\n{self.code_style_guidelines}\n"
            if self._has_text(self.writing_style_guidelines):
                md += (
                    f"\n### WRITING STYLE GUIDELINES\n{self.writing_style_guidelines}\n"
                )
        if self._has_text(self.guardrails):
            md += f"\n## GUARDRAILS{self.guardrails}\n"
        if self._has_text(self.failure_protocol):
            md += (
                "\n## FAILURE PROTOCOL\n"
                "In case of a failure follow the below steps:\n"
                f"{self.failure_protocol}\n"
            )
        md = re.sub(r"[\r\n][\r\n]{2,}", "\n\n", md)
        return md
