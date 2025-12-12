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
#import argparse
from enum import Enum
from openai import OpenAI
#from typing import Optional

prompt = \
"""You are 'Ten Minute Lessons', an experimental micro-learning engine.
    The focus is on learning speed, so:
        - Use short paragraphs and simple line breaks.
        - Do NOT use Markdown (no bullets, no bold, no headings with #).
        - Use clear text labels like: [TITLE]:, [GOALS]:, [LESSON#]:, [SUMMARY]:, etc.
        - Each lesson should take no more than 2-3 minutes to read each.

Your job:
    - Teach the requested topic at a shallow, beginner-friendly level.
    - Break the topic into 3 micro-lessons (precede with [Lesson#]).
    - Each micro-lesson should take no more than 2-3 minutes to read.
    - After each lesson, ask exactly two understanding-check questions based upon the content (precede with [Question#.#] where first # is lesson number and second # is question number).
    - At the end, give a short [SUMMARY].

Here is your task, please teach about this:
"""

qprompt = \
"""Below is a question and an answer.  Please assess the answer for the question and provide a short response for the user.
   This could be as simple as Correct, if the answer is correct, or a brief response of the correct answer.  Include no more
   than a sentence, but be as concise as possible.
"""

class TMLEngine():

    def __init__(self):
        self.llm_client = OpenAIClient( )
        request = "What would you like to learn about? "
        self.emit_with_tick(request, 25)
        self.user_topic = input()
        self.prompt = prompt+self.user_topic

    def paginate_text(self, text: str) -> str:
        width = 80
        words = str(text).split()
        if not words:
            return ""

        lines = []
        current_line = words[0]

        for word in words[1:]:
            # If adding the next word exceeds the width, start a new line
            if len(current_line) + 1 + len(word) > width:
                lines.append(current_line)
                current_line = word
            else:
                current_line += " " + word

        lines.append(current_line)
        return "\n".join(lines)

    def extract_section(self, full_text, section_name):
        # Matches exact header name, with optional spaces before colon
        header_regex = rf'^\[{re.escape(section_name)}\]\s*:(.*)$'
        # Matches ANY header of the form [Something]:
        any_header_regex = r'^\[.*?\]\s*:'

        lines = full_text.splitlines()
        collecting = False
        result = []

        for line in lines:
            # Is this ANY header?
            if re.match(any_header_regex, line):
                if collecting:
                    # We hit the next header: stop collecting
                    break

                # Is this the header we want?
                m = re.match(header_regex, line)
                if m:
                    collecting = True
                    first_line_content = m.group(1).strip()
                    if first_line_content:
                        result.append(first_line_content)
                continue

            # If collecting, add follow-up lines
            if collecting:
                result.append(line)

        return "\n".join(result).rstrip()

    def emit_with_tick(self, text, tick_ms=15):
        tick = tick_ms / 1000.0
        for ch in text:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(tick)

    def flow(self):
        learning_plan: str = self.llm_client.execute_prompt( self.prompt )

        print(learning_plan)

        title = self.extract_section(learning_plan, "TITLE")
        self.emit_with_tick(title+"\n\n")

        print("Goals:")
        goals = self.extract_section(learning_plan, "GOALS")
        self.emit_with_tick(goals+"\n\n")

        lesson = 1
        while (lesson <= 3):

            lesson_text = self.paginate_text(self.extract_section(learning_plan, f"LESSON {lesson}"))
            print(f"Lesson {lesson}")
            self.emit_with_tick(lesson_text+"\n\n")

            question = 1
            while (question <= 2):
                question_text = self.paginate_text(self.extract_section(learning_plan, f"Question {lesson}.{question}"))
                self.emit_with_tick(question_text+"\n\n")
                answer = input()

                response: str = self.paginate_text(self.llm_client.execute_prompt( f"{qprompt}\n {question_text}\n {answer}\n"))
                
                self.emit_with_tick("\n" + response + "\n\n")

                question = question + 1
            
            lesson = lesson + 1

        summary = self.paginate_text(self.extract_section(learning_plan, f"SUMMARY"))
        self.emit_with_tick("\n" + summary + "\n\n")

        self.emit_with_tick("\nThanks for learning with Ten Minute Lessons!\n\n")


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
