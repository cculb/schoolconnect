"""Unit tests for communication skills.

This module tests the structure and content of parent-teacher communication skills:
- teacher-meeting-prep.md
- draft-teacher-email.md
- communication-suggestions.md

Tests validate:
- YAML frontmatter structure
- Email templates follow professional parent-teacher tone
- MCP tool references match server.py definitions
- Markdown structure and formatting
"""

import re
from pathlib import Path

import pytest
import yaml

# Test constants
SKILLS_DIR = Path(__file__).parent.parent.parent / ".claude" / "skills"
MCP_TOOLS = {
    "prepare_teacher_meeting",
    "draft_teacher_email",
    "get_communication_suggestions",
    "get_teacher_comments",
    "list_teachers",
    "get_teacher_profile",
    "get_missing_assignments",
    "get_current_grades",
    "get_course_score_details",
}


class TestTeacherMeetingPrepSkill:
    """Tests for teacher-meeting-prep.md skill."""

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the skill file."""
        return SKILLS_DIR / "teacher-meeting-prep.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Read skill file content."""
        assert skill_path.exists(), f"Skill file not found: {skill_path}"
        return skill_path.read_text()

    @pytest.fixture
    def frontmatter(self, skill_content: str) -> dict:
        """Extract YAML frontmatter."""
        match = re.match(r"^---\n(.*?)\n---", skill_content, re.DOTALL)
        assert match, "No YAML frontmatter found"
        return yaml.safe_load(match.group(1))

    def test_frontmatter_structure(self, frontmatter: dict):
        """Test YAML frontmatter has required fields."""
        assert "description" in frontmatter, "Missing 'description' field"
        assert isinstance(frontmatter["description"], str)
        assert len(frontmatter["description"]) > 20, "Description too short"

    def test_frontmatter_description(self, frontmatter: dict):
        """Test description is relevant to teacher meetings."""
        desc = frontmatter["description"].lower()
        assert any(
            keyword in desc for keyword in ["meeting", "teacher", "conference", "talking points"]
        ), "Description should mention meeting/teacher/conference/talking points"

    def test_references_mcp_tool(self, skill_content: str):
        """Test skill references prepare_teacher_meeting MCP tool."""
        assert "prepare_teacher_meeting" in skill_content, (
            "Should reference prepare_teacher_meeting MCP tool"
        )

    def test_markdown_structure(self, skill_content: str):
        """Test markdown has proper structure."""
        # Should have headers
        assert re.search(r"^#{1,3}\s+\w+", skill_content, re.MULTILINE), "Should have headers"

        # Should have content after frontmatter
        content_after_frontmatter = re.sub(r"^---\n.*?\n---\n", "", skill_content, flags=re.DOTALL)
        assert len(content_after_frontmatter.strip()) > 100, "Should have substantial content"

    def test_suggests_questions(self, skill_content: str):
        """Test skill provides guidance on asking questions."""
        content_lower = skill_content.lower()
        assert any(
            keyword in content_lower for keyword in ["question", "ask", "discuss", "talk about"]
        ), "Should provide guidance on questions to ask"


class TestDraftTeacherEmailSkill:
    """Tests for draft-teacher-email.md skill."""

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the skill file."""
        return SKILLS_DIR / "draft-teacher-email.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Read skill file content."""
        assert skill_path.exists(), f"Skill file not found: {skill_path}"
        return skill_path.read_text()

    @pytest.fixture
    def frontmatter(self, skill_content: str) -> dict:
        """Extract YAML frontmatter."""
        match = re.match(r"^---\n(.*?)\n---", skill_content, re.DOTALL)
        assert match, "No YAML frontmatter found"
        return yaml.safe_load(match.group(1))

    def test_frontmatter_structure(self, frontmatter: dict):
        """Test YAML frontmatter has required fields."""
        assert "description" in frontmatter, "Missing 'description' field"
        assert isinstance(frontmatter["description"], str)
        assert len(frontmatter["description"]) > 20, "Description too short"

    def test_frontmatter_description(self, frontmatter: dict):
        """Test description is relevant to email drafting."""
        desc = frontmatter["description"].lower()
        assert any(
            keyword in desc for keyword in ["email", "draft", "write", "teacher", "message"]
        ), "Description should mention email/draft/write/teacher/message"

    def test_references_mcp_tool(self, skill_content: str):
        """Test skill references draft_teacher_email MCP tool."""
        assert "draft_teacher_email" in skill_content, (
            "Should reference draft_teacher_email MCP tool"
        )

    def test_email_topics_coverage(self, skill_content: str):
        """Test skill covers all email topics."""
        content_lower = skill_content.lower()
        topics = ["missing_work", "grade_concern", "general", "meeting_request"]

        # Should mention at least 3 of 4 topics
        topics_found = sum(1 for topic in topics if topic.replace("_", " ") in content_lower)
        assert topics_found >= 3, f"Should mention at least 3 email topics, found {topics_found}"

    def test_professional_tone_guidance(self, skill_content: str):
        """Test skill emphasizes professional tone."""
        content_lower = skill_content.lower()
        assert any(
            keyword in content_lower
            for keyword in ["professional", "respectful", "polite", "courteous", "formal"]
        ), "Should mention professional tone"

    def test_markdown_structure(self, skill_content: str):
        """Test markdown has proper structure."""
        # Should have headers
        assert re.search(r"^#{1,3}\s+\w+", skill_content, re.MULTILINE), "Should have headers"

        # Should have content after frontmatter
        content_after_frontmatter = re.sub(r"^---\n.*?\n---\n", "", skill_content, flags=re.DOTALL)
        assert len(content_after_frontmatter.strip()) > 100, "Should have substantial content"

    def test_example_template(self, skill_content: str):
        """Test skill provides example email template."""
        # Should have example showing professional structure
        assert any(
            keyword in skill_content for keyword in ["Dear", "example", "template", "Subject"]
        ), "Should provide example email template"


class TestCommunicationSuggestionsSkill:
    """Tests for communication-suggestions.md skill."""

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the skill file."""
        return SKILLS_DIR / "communication-suggestions.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Read skill file content."""
        assert skill_path.exists(), f"Skill file not found: {skill_path}"
        return skill_path.read_text()

    @pytest.fixture
    def frontmatter(self, skill_content: str) -> dict:
        """Extract YAML frontmatter."""
        match = re.match(r"^---\n(.*?)\n---", skill_content, re.DOTALL)
        assert match, "No YAML frontmatter found"
        return yaml.safe_load(match.group(1))

    def test_frontmatter_structure(self, frontmatter: dict):
        """Test YAML frontmatter has required fields."""
        assert "description" in frontmatter, "Missing 'description' field"
        assert isinstance(frontmatter["description"], str)
        assert len(frontmatter["description"]) > 20, "Description too short"

    def test_frontmatter_description(self, frontmatter: dict):
        """Test description is relevant to communication suggestions."""
        desc = frontmatter["description"].lower()
        assert any(
            keyword in desc for keyword in ["suggestion", "recommend", "when to", "contact"]
        ), "Description should mention suggestions/recommendations"

    def test_references_mcp_tool(self, skill_content: str):
        """Test skill references get_communication_suggestions MCP tool."""
        assert "get_communication_suggestions" in skill_content, (
            "Should reference get_communication_suggestions MCP tool"
        )

    def test_data_driven_approach(self, skill_content: str):
        """Test skill emphasizes data-driven suggestions."""
        content_lower = skill_content.lower()
        assert any(
            keyword in content_lower
            for keyword in [
                "missing work",
                "grade",
                "attendance",
                "pattern",
                "trend",
                "data",
            ]
        ), "Should mention data sources for suggestions"

    def test_priority_guidance(self, skill_content: str):
        """Test skill discusses prioritization."""
        content_lower = skill_content.lower()
        assert any(
            keyword in content_lower for keyword in ["priority", "urgent", "important", "critical"]
        ), "Should discuss prioritization of communications"

    def test_markdown_structure(self, skill_content: str):
        """Test markdown has proper structure."""
        # Should have headers
        assert re.search(r"^#{1,3}\s+\w+", skill_content, re.MULTILINE), "Should have headers"

        # Should have content after frontmatter
        content_after_frontmatter = re.sub(r"^---\n.*?\n---\n", "", skill_content, flags=re.DOTALL)
        assert len(content_after_frontmatter.strip()) > 100, "Should have substantial content"


class TestMCPToolReferences:
    """Tests for MCP tool references across all communication skills."""

    @pytest.fixture
    def all_skills_content(self) -> dict[str, str]:
        """Read all communication skill files."""
        skills = {}
        for skill_file in [
            "teacher-meeting-prep.md",
            "draft-teacher-email.md",
            "communication-suggestions.md",
        ]:
            path = SKILLS_DIR / skill_file
            if path.exists():
                skills[skill_file] = path.read_text()
        return skills

    def test_valid_mcp_tool_references(self, all_skills_content: dict[str, str]):
        """Test all MCP tool references are valid."""
        for skill_name, content in all_skills_content.items():
            # Find all potential MCP tool references (snake_case identifiers)
            potential_tools = re.findall(r"\b([a-z_]+_[a-z_]+)\b", content)

            for tool in potential_tools:
                # Skip common non-tool words
                if tool in [
                    "parent_teacher",
                    "teacher_name",
                    "student_name",
                    "school_connect",
                ]:
                    continue

                # If it looks like an MCP tool (ends with common verbs)
                if any(
                    tool.endswith(suffix)
                    for suffix in ["_meeting", "_email", "_suggestions", "_comments", "_teachers"]
                ):
                    assert tool in MCP_TOOLS, (
                        f"Invalid MCP tool '{tool}' referenced in {skill_name}"
                    )

    def test_no_hardcoded_data(self, all_skills_content: dict[str, str]):
        """Test skills don't contain hardcoded student/teacher data."""
        for skill_name, content in all_skills_content.items():
            # Remove frontmatter and code blocks
            content_cleaned = re.sub(r"^---\n.*?\n---", "", content, flags=re.DOTALL)
            content_cleaned = re.sub(r"```.*?```", "", content_cleaned, flags=re.DOTALL)

            # Should not have specific student names (common test names)
            assert not re.search(r"\b(John|Jane|Alice|Bob|Charlie)\s+\w+", content_cleaned), (
                f"Should not contain hardcoded student names in {skill_name}"
            )


class TestProfessionalToneValidation:
    """Tests for professional parent-teacher communication tone."""

    @pytest.fixture
    def email_skill_content(self) -> str:
        """Read draft-teacher-email.md skill."""
        path = SKILLS_DIR / "draft-teacher-email.md"
        assert path.exists(), "draft-teacher-email.md not found"
        return path.read_text()

    def test_formal_greeting(self, email_skill_content: str):
        """Test email examples use formal greetings."""
        # Should show "Dear" as example greeting
        assert "Dear" in email_skill_content, "Should use 'Dear' for formal greeting"

    def test_professional_closing(self, email_skill_content: str):
        """Test email examples use professional closing."""
        content_lower = email_skill_content.lower()
        assert any(
            closing in content_lower
            for closing in ["best regards", "sincerely", "thank you", "regards"]
        ), "Should use professional closing"

    def test_avoids_casual_language(self, email_skill_content: str):
        """Test email examples avoid casual language in actual email templates."""
        # Extract only the example email sections (after "Example Email Structure")
        example_section_match = re.search(
            r"## Example Email Structure.*$", email_skill_content, re.DOTALL
        )

        if example_section_match:
            example_content = example_section_match.group(0).lower()

            # Should not use overly casual terms in email examples
            # Note: "hey" might appear in the "don'ts" section, which is fine
            casual_greetings = ["hey there", "what's up", "yo ", "sup "]
            for term in casual_greetings:
                assert term not in example_content, (
                    f"Email examples should avoid casual greeting '{term}'"
                )

    def test_respectful_tone_keywords(self, email_skill_content: str):
        """Test email examples include respectful language."""
        content_lower = email_skill_content.lower()

        # Should include respectful phrases
        respectful_phrases = [
            "please",
            "thank you",
            "appreciate",
            "hope",
            "understand",
        ]
        found_phrases = sum(1 for phrase in respectful_phrases if phrase in content_lower)
        assert found_phrases >= 3, (
            f"Should include at least 3 respectful phrases, found {found_phrases}"
        )


class TestSkillUsabilityAndQuality:
    """Tests for overall usability and quality of communication skills."""

    @pytest.fixture
    def all_skills(self) -> dict[str, Path]:
        """All communication skill file paths."""
        return {
            "teacher-meeting-prep": SKILLS_DIR / "teacher-meeting-prep.md",
            "draft-teacher-email": SKILLS_DIR / "draft-teacher-email.md",
            "communication-suggestions": SKILLS_DIR / "communication-suggestions.md",
        }

    def test_all_skills_exist(self, all_skills: dict[str, Path]):
        """Test all required skill files exist."""
        for name, path in all_skills.items():
            assert path.exists(), f"Missing skill file: {name} at {path}"

    def test_skills_are_readable(self, all_skills: dict[str, Path]):
        """Test all skills can be read and have content."""
        for name, path in all_skills.items():
            content = path.read_text()
            assert len(content) > 50, f"Skill {name} has insufficient content"

    def test_skills_have_unique_content(self, all_skills: dict[str, Path]):
        """Test each skill has unique, non-duplicated content."""
        contents = {}
        for name, path in all_skills.items():
            content = path.read_text()
            # Remove frontmatter for comparison
            content_body = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)
            contents[name] = content_body

        # Check each pair is sufficiently different
        skills_list = list(contents.keys())
        for i, skill1 in enumerate(skills_list):
            for skill2 in skills_list[i + 1 :]:
                # Skills should not be 90%+ identical
                common_chars = sum(
                    1 for c1, c2 in zip(contents[skill1], contents[skill2]) if c1 == c2
                )
                min_length = min(len(contents[skill1]), len(contents[skill2]))
                similarity = common_chars / min_length if min_length > 0 else 0

                assert similarity < 0.9, (
                    f"Skills {skill1} and {skill2} are too similar ({similarity:.1%})"
                )

    def test_no_placeholder_text(self, all_skills: dict[str, Path]):
        """Test skills don't contain placeholder text."""
        placeholders = ["TODO", "FIXME", "XXX", "[placeholder]", "TBD"]

        for name, path in all_skills.items():
            content = path.read_text()
            for placeholder in placeholders:
                assert placeholder not in content, (
                    f"Skill {name} contains placeholder text: {placeholder}"
                )

    def test_consistent_formatting(self, all_skills: dict[str, Path]):
        """Test all skills use consistent markdown formatting."""
        for name, path in all_skills.items():
            content = path.read_text()

            # All skills should start with YAML frontmatter
            assert content.startswith("---\n"), f"Skill {name} should start with YAML frontmatter"

            # All skills should have at least one heading
            assert re.search(r"^#+\s+", content, re.MULTILINE), (
                f"Skill {name} should have at least one heading"
            )
