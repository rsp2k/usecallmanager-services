"""Cisco IP Phone XML response builders.

Generates XML objects for Cisco 7900/7800/8800 series IP phones.
7900 series require different prompts and softkey positions.
"""

from html import escape
from urllib.parse import quote_plus


class CiscoIPPhoneXML:
    """Base class for Cisco IP Phone XML responses."""

    def __init__(self, is_79xx: bool = False):
        self.is_79xx = is_79xx
        self._softkeys: list[str] = []

    def softkey_position(self, role: str) -> str:
        """Get softkey position based on phone model and role.

        7900 series: Exit=3, Select=1, Update=2, Next=2, Previous=4
        7800/8800:   Exit=1, Select=2, Update=3, Next=3, Previous=4
        """
        if self.is_79xx:
            positions = {"exit": "3", "select": "1", "update": "2", "next": "2", "previous": "4"}
        else:
            positions = {"exit": "1", "select": "2", "update": "3", "next": "3", "previous": "4"}
        return positions.get(role, "1")

    def add_softkey(self, name: str, url: str, position: str) -> "CiscoIPPhoneXML":
        """Add a softkey item."""
        self._softkeys.append(
            f"  <SoftKeyItem>\n"
            f"    <Name>{escape(name)}</Name>\n"
            f"    <Position>{position}</Position>\n"
            f"    <URL>{escape(url)}</URL>\n"
            f"  </SoftKeyItem>\n"
        )
        return self

    def _build_softkeys(self) -> str:
        """Build softkey XML string."""
        return "".join(self._softkeys)


class CiscoIPPhoneMenu(CiscoIPPhoneXML):
    """Menu XML builder with MenuItem entries."""

    def __init__(self, title: str, is_79xx: bool = False):
        super().__init__(is_79xx)
        self.title = title
        self._items: list[tuple[str, str]] = []

    def add_item(self, name: str, url: str) -> "CiscoIPPhoneMenu":
        """Add a menu item."""
        self._items.append((name, url))
        return self

    def build(self) -> str:
        """Build the XML string."""
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<CiscoIPPhoneMenu>\n"
            f"  <Title>{escape(self.title)}</Title>\n"
        )

        for name, url in self._items:
            xml += (
                "  <MenuItem>\n"
                f"    <Name>{escape(name)}</Name>\n"
                f"    <URL>{escape(url)}</URL>\n"
                "  </MenuItem>\n"
            )

        if self.is_79xx:
            xml += "  <Prompt>Your current options</Prompt>\n"

        xml += self._build_softkeys()
        xml += "</CiscoIPPhoneMenu>\n"
        return xml


class CiscoIPPhoneDirectory(CiscoIPPhoneXML):
    """Directory XML builder with DirectoryEntry entries."""

    def __init__(self, title: str, is_79xx: bool = False, prompt: str | None = None):
        super().__init__(is_79xx)
        self.title = title
        self.prompt = prompt
        self._entries: list[tuple[str, str]] = []

    def add_entry(self, name: str, telephone: str) -> "CiscoIPPhoneDirectory":
        """Add a directory entry."""
        self._entries.append((name, telephone))
        return self

    def build(self) -> str:
        """Build the XML string."""
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<CiscoIPPhoneDirectory>\n"
            f"  <Title>{escape(self.title)}</Title>\n"
        )

        for name, telephone in self._entries:
            xml += (
                "  <DirectoryEntry>\n"
                f"    <Name>{escape(name)}</Name>\n"
                f"    <Telephone>{quote_plus(telephone)}</Telephone>\n"
                "  </DirectoryEntry>\n"
            )

        if self.is_79xx:
            prompt_text = self.prompt or "Select entry"
            xml += f"  <Prompt>{escape(prompt_text)}</Prompt>\n"

        xml += self._build_softkeys()
        xml += "</CiscoIPPhoneDirectory>\n"
        return xml


class CiscoIPPhoneText(CiscoIPPhoneXML):
    """Text display XML builder."""

    def __init__(self, title: str, text: str, is_79xx: bool = False):
        super().__init__(is_79xx)
        self.title = title
        self.text = text

    def build(self) -> str:
        """Build the XML string."""
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<CiscoIPPhoneText>\n"
            f"  <Title>{escape(self.title)}</Title>\n"
            f"  <Text>{escape(self.text)}</Text>\n"
        )

        if self.is_79xx:
            xml += "  <Prompt>Your current options</Prompt>\n"

        xml += self._build_softkeys()
        xml += "</CiscoIPPhoneText>\n"
        return xml
