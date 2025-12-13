#!/usr/bin/env python3

# Ten Minute Lessons; a Micro-Learning tool.
# mtj@mtjones.com
# December 1st, 2025

import os
import re
import sys
import time
import string
import logging
from enum import IntEnum
from openai import OpenAI

prompt = \
"""You are 'Ten Minute Lessons', an experimental micro-learning engine.
    The focus is on learning speed, so:
        - Use short paragraphs and simple line breaks.
        - Do NOT use Markdown (no bullets, no bold, no headings with #).
        - Use clear text labels like: [TITLE]:, [GOALS]:, [LESSON#]:, [QUESTION#.#], [SUMMARY]:, etc.

Your job:
    - Teach the requested topic at a beginner-friendly level.
    - Break the topic into 3 micro-lessons (precede with [Lesson#]).
    - Each micro-lesson should take no more than 4-5 minutes to read.
    - After each lesson, ask exactly two understanding-check questions based upon the content (precede with [QUESTION#.#] where first # is lesson number and second # is question number).
    - At the end, give a short [SUMMARY].

Here's the format to follow:
[TITLE]
***Title***
[GOALS]
***One or more goals, each on a separate line.***
[LESSON1]
***Text for lesson 1***
[QUESTION1.1]
***Question 1 for lesson 1***
[QUESTION1.2]
***Question 2 for lesson 1***
[LESSON2]
***Text for lesson 1***
[QUESTION2.1]
***Question 1 for lesson 2***
[QUESTION2.2]
***Question 2 for lesson 2***
[LESSON3]
***Text for lesson 1***
[QUESTION3.1]
***Question 1 for lesson 3***
[QUESTION3.2]
***Question 2 for lesson 3***
[SUMMARY]
***Summary text***

Here is your task, please teach about this:
"""

qprompt = \
"""Below is a question and an answer.  Please assess the answer for the question and provide a short response for the user.
   This could be as simple as Correct, if the answer is correct, or a brief response of the correct answer.  Include no more
   than a sentence, but be as concise as possible.
"""

class Color(IntEnum):
  WHITE = 37
  GREEN = 32
  YELLOW = 33

class TMLEngine():

    def __init__(self):
        self.llm_client = OpenAIClient( )
        request = "What would you like to learn about? "
        self.emit_with_tick(request, 25)
        self.user_topic = input()
        self.prompt = prompt+self.user_topic

    def paginate_text(self, text: str, indent: int = 0) -> str:
        width = 80
        words = str(text).split()
        if not words:
            return ""

        lines = []
        current_line = words[0]

        for word in words[1:]:
            # If adding the next word exceeds the width, start a new line
            if len(current_line) + 1 + indent + len(word) > width:
                lines.append(" "*indent + current_line)
                current_line = word
            else:
                current_line += " " + word

        lines.append(current_line)
        return "\n".join(lines)

    def extract_section(self, text: str, section: str) -> str:
        pattern = rf"\[{re.escape(section)}\]\s*(.*?)(?=\n\s*\[|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    def emit_with_tick(self, text, color: Color = Color.WHITE, tick_ms=15):
        tick = tick_ms / 1000.0

        sys.stdout.write(f"\033[{int(color)}m")

        for ch in text:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(tick)

        sys.stdout.write("\033[0m")

    def flow(self):
        learning_plan: str = self.llm_client.execute_prompt( self.prompt )

        title = self.extract_section(learning_plan, "TITLE")
        self.emit_with_tick("\n"+title+"\n\n")

        self.emit_with_tick("Goals:\n")
        goals = self.extract_section(learning_plan, "GOALS")
        self.emit_with_tick(goals+"\n\n", Color.GREEN)

        lesson = 1
        while (lesson <= 3):

            lesson_text = self.paginate_text(self.extract_section(learning_plan, f"LESSON{lesson}"))
            print(f"Lesson {lesson}")
            self.emit_with_tick(lesson_text+"\n\n", Color.GREEN)

            question = 1
            while (question <= 2):
                question_text = self.paginate_text(self.extract_section(learning_plan, f"QUESTION{lesson}.{question}"))
                self.emit_with_tick(question_text+"\n\n", Color.YELLOW)
                answer = input(" "*4)

                response: str = self.paginate_text(self.llm_client.execute_prompt( f"{qprompt}\n {question_text}\n {answer}\n"))
                
                self.emit_with_tick("\n" + response + "\n\n", Color.GREEN)

                question = question + 1
            
            lesson = lesson + 1

        summary = self.paginate_text(self.extract_section(learning_plan, f"SUMMARY"))
        self.emit_with_tick("\n" + summary + "\n\n", Color.GREEN)

        self.emit_with_tick("\nThanks for learning with Ten Minute Lessons!\n\n", Color.GREEN)


class OpenAIClient():
    """Simple Client for interaction with OpenAI API."""

    def __init__(self):
        """Initializes the LLMClient with the OpenAI API key."""
        self.openai_key = self._get_openai_key( )

    @staticmethod
    def _get_openai_key( ) -> str:
        """Get the OPENAI Key from the environment variables."""
        openai_key = os.environ.get( 'OPENAI_KEY', None )
        if openai_key is None:
            logging.error( "OPENAI_KEY is not set\n" )
            sys.exit(1)
        return openai_key

    def execute_prompt( self, message: str ) -> str | None:
        """Executes the prompt against the OpenAI API and returns the response."""
        client = OpenAI( api_key = self.openai_key )

        chat_completion = client.chat.completions.create(
            messages = [ { "role": "user", "content": message, } ],
            model="gpt-4o",
        )

        return str(chat_completion.choices[0].message.content)


def main( ) -> None:
    """Main function for script execution."""
    engine = TMLEngine()
    engine.flow()


if __name__ == "__main__":
    main( )
    sys.exit(0)
