from dataclasses import dataclass
from enum import auto, Enum
import json
from typing import Optional

from PIL.Image import Image

TOOL_PROMPT = 'Answer the following questions as best as you can. You have access to the following tools:\n'


class Role(Enum):
    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()
    TOOL = auto()
    INTERPRETER = auto()
    OBSERVATION = auto()

    def __str__(self):
        if self == Role.SYSTEM:
            return "<|system|>"
        elif self == Role.USER:
            return "<|user|>"
        elif self == Role.ASSISTANT or Role.TOOL or Role.INTERPRETER:
            return "<|assistant|>"
        elif self == Role.OBSERVATION:
            return "<|observation|>"
        # match self:
        #     case Role.SYSTEM:
        #         return "<|system|>"
        #     case Role.USER:
        #         return "<|user|>"
        #     case Role.ASSISTANT | Role.TOOL | Role.INTERPRETER:
        #         return "<|assistant|>"
        #     case Role.OBSERVATION:
        #         return "<|observation|>"

    # Get the message block for the given role
    # def get_message(self):
    #     # Compare by value here, because the enum object in the session state
    #     # is not the same as the enum cases here, due to streamlit's rerunning
    #     # behavior.
    #     match self.value:
    #         case Role.SYSTEM.value:
    #             return
    #         case Role.USER.value:
    #             return st.chat_message(name="user", avatar="user")
    #         case Role.ASSISTANT.value:
    #             return st.chat_message(name="assistant", avatar="assistant")
    #         case Role.TOOL.value:
    #             return st.chat_message(name="tool", avatar="assistant")
    #         case Role.INTERPRETER.value:
    #             return st.chat_message(name="interpreter", avatar="assistant")
    #         case Role.OBSERVATION.value:
    #             return st.chat_message(name="observation", avatar="user")
    #         case _:
    #             st.error(f'Unexpected role: {self}')


@dataclass
class Conversation:
    role: Role
    content: str
    width: int
    height: int
    tool: Optional[str] = None
    image: Optional[Image] = None

    def __str__(self) -> str:
        print(self.role, self.content, self.tool)
        if self.role == Role.SYSTEM or Role.USER or Role.ASSISTANT or Role.OBSERVATION:
            return f'{self.role}\n{self.content}'
        elif self.role == Role.TOOL:
            return f'{self.role}{self.tool}\n{self.content}'
        elif self.role == Role.INTERPRETER:
            return f'{self.role}interpreter\n{self.content}'
        # match self.role:
        #     case Role.SYSTEM | Role.USER | Role.ASSISTANT | Role.OBSERVATION:
        #         return f'{self.role}\n{self.content}'
        #     case Role.TOOL:
        #         return f'{self.role}{self.tool}\n{self.content}'
        #     case Role.INTERPRETER:
        #         return f'{self.role}interpreter\n{self.content}'

    # Human readable format
    def get_text(self) -> str:
        text = postprocess_text(self.content)
        if self.role.value == Role.TOOL.value:
            text = f'Calling tool `{self.tool}`:\n\n{text}'
        elif self.role.value == Role.INTERPRETER.value:
            text = f'{text}'
        elif self.role.value == Role.OBSERVATION.value:
            text = f'Observation:\n```\n{text}\n```'
        # match self.role.value:
        #     case Role.TOOL.value:
        #         text = f'Calling tool `{self.tool}`:\n\n{text}'
        #     case Role.INTERPRETER.value:
        #         text = f'{text}'
        #     case Role.OBSERVATION.value:
        #         text = f'Observation:\n```\n{text}\n```'
        return text

    # Display as a markdown block
    # def show(self, placeholder: DeltaGenerator | None=None) -> str:
    #     if placeholder:
    #         message = placeholder
    #     else:
    #         message = self.role.get_message()
    #     if self.image:
    #         message.image(self.image)
    #     else:
    #         text = self.get_text()
    #         message.markdown(text)


def preprocess_text(
        system: Optional[str],
        tools: Optional[list[dict]],
        history: list[Conversation],
) -> str:
    if tools:
        tools = json.dumps(tools, indent=4, ensure_ascii=False)

    prompt = f"{Role.SYSTEM}\n"
    prompt += system if not tools else TOOL_PROMPT
    if tools:
        tools = json.loads(tools)
        prompt += json.dumps(tools, ensure_ascii=False)
    for conversation in history:
        prompt += f'{conversation}'
    prompt += f'{Role.ASSISTANT}\n'
    return prompt


def postprocess_text(text: str) -> str:
    text = text.replace("\(", "$")
    text = text.replace("\)", "$")
    text = text.replace("\[", "$$")
    text = text.replace("\]", "$$")
    text = text.replace("<|assistant|>", "")
    text = text.replace("<|observation|>", "")
    text = text.replace("<|system|>", "")
    text = text.replace("<|user|>", "")
    return text.strip()


def append_conversation(
        conversation: Conversation,
        history: list[Conversation],
) -> None:
    history.append(conversation)
