from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema


class ResearchQuestion(BaseModel):
    question_text: str = Field(default_factory=str)
    research_subquestions: Optional[List[str]] = Field(default_factory=list)


class ResearchPlan(BaseModel):
    created_at: SkipJsonSchema[datetime] = Field(
        default_factory=datetime.now,
    )
    title: str = Field(default_factory=str)
    summary: str = Field(default_factory=str)
    objectives: List[str] = Field(default_factory=list)
    keywords: Optional[List[str]] = Field(default_factory=list)
    research_questions: List[ResearchQuestion] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    further_clarifications_required: List[str] = Field(default_factory=list)
    other_ai_message: str = Field(default_factory=str)

    def to_markdown(self) -> str:
        """Converts the ResearchPlan object into a structured Markdown document."""
        timestamp = self.created_at.strftime("%Y-%m-%d %H:%M")

        title = self.title.lstrip("# ").strip() or "Untitled Research Plan"
        md = f"# {title}\nAuthor: Lattice, {timestamp}\n\n"

        # Summary Section
        if self.summary.strip():
            md += f"## Summary\n{self.summary.strip()}\n\n"

        # Objectives Section
        objectives = [o.strip() for o in self.objectives if o.strip()]
        if objectives:
            md += "## Objectives\n"
            for obj in objectives:
                md += f"- {obj}\n"
            md += "\n"

        # Keywords Section
        keywords = [k.strip() for k in self.keywords or [] if k.strip()]
        if keywords:
            md += "## Keywords\n"
            md += ", ".join(f"`{k}`" for k in keywords) + "\n\n"

        # Research Questions Section
        questions = [
            rq
            for rq in self.research_questions
            if rq.question_text.strip()
            or any(s.strip() for s in rq.research_subquestions or [])
        ]

        if questions:
            md += "## Research Questions\n"
            for i, rq in enumerate(questions, 1):
                q_text = rq.question_text.lstrip("# ").strip()
                md += f"### **RQ{i}**: {q_text}\n"

                for j, sub in enumerate(rq.research_subquestions or [], 1):
                    sub_text = sub.strip()
                    if sub_text:
                        md += f"- **Sub-RQ{j}**: {sub_text}\n"
                md += "\n"

        # Next Steps
        next_steps = [s.strip() for s in self.next_steps if s.strip()]
        if next_steps:
            md += "## Next Steps\n"
            for i, step in enumerate(next_steps, 1):
                md += f"{i}. {step}\n"
            md += "\n"

        # Further Clarifications Required
        clarifications = [
            c.strip() for c in self.further_clarifications_required if c.strip()
        ]
        if clarifications:
            md += "## Further Clarifications Required\n"
            for i, item in enumerate(clarifications, 1):
                md += f"{i}. {item}\n"
            md += "\n"

        return md

    def is_empty(self) -> bool:
        def has_text(s: str | None) -> bool:
            return bool(s and s.strip())

        # Title or summary
        if has_text(self.title):
            return False
        if has_text(self.summary):
            return False

        # Objectives
        if any(has_text(o) for o in self.objectives or []):
            return False

        # Keywords
        if any(has_text(k) for k in self.keywords or []):
            return False

        # Research questions and subquestions
        for rq in self.research_questions or []:
            if has_text(rq.question_text):
                return False
            if any(has_text(s) for s in rq.research_subquestions or []):
                return False

        # Next steps
        if any(has_text(s) for s in self.next_steps):
            return False

        # Further clarifications
        if any(has_text(c) for c in self.further_clarifications_required):
            return False

        return True


RESEARCH_PLAN_TEMPLATE = ResearchPlan(
    title="Title",
    summary="Summary",
    objectives=["objective1", "objective2"],
    keywords=["keyword1", "keyword2"],
    research_questions=[
        ResearchQuestion(
            question_text="ResearchQuestion1",
            research_subquestions=["ResearchSubQuestion1", "ResearchSubQuestion2"],
        )
    ],
    further_clarifications_required=[
        "further clarification 1",
        "further clarification 2",
    ],
    next_steps=["step 1", "step 2"],
    other_ai_message="other ai messages/comments here",
)
